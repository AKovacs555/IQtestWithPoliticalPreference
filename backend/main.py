import os
import hashlib
import hmac
import secrets
import random
import time
from typing import List, Optional

import sys
import os

# Add the repository root (parent directory of backend) to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException, Header
import io
import contextlib
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import tempfile
from tools.generate_questions import import_dir

from sms_service import send_otp, SMS_PROVIDER
from features import (
    leaderboard_by_party,
    generate_share_image,
    update_normative_distribution,
    dp_average,
    MIN_BUCKET_SIZE,
)
from demographics import collect_demographics
from party import update_party_affiliation
from dp import add_laplace

from questions import (
    DEFAULT_QUESTIONS,
    QUESTION_MAP,
    get_random_questions,
    available_sets,
)
from adaptive import select_next_question, should_stop
from irt import update_theta, percentile
from scoring import (
    estimate_theta,
    iq_score,
    ability_summary,
    standard_error,
)
from payment import select_processor
from analytics import log_event
from tools.dif_analysis import dif_report
from routes.exam import router as exam_router
import json

app = FastAPI()
app.state.sessions = {}

@app.on_event("startup")
async def on_startup():
    await init_db()

# CORS for SPA
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exam_router)

# SMS provider handled by sms_service module

# Database placeholder (Supabase)
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Number of questions per quiz session
NUM_QUESTIONS = int(os.getenv("NUM_QUESTIONS", "20"))

# Maximum free attempts before payment is required
MAX_FREE_ATTEMPTS = int(os.getenv("MAX_FREE_ATTEMPTS", "1"))

from supabase import create_client
from sqlalchemy import select
from db import AsyncSessionLocal, User, init_db
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY", "")
supabase = None
if SUPABASE_URL and SUPABASE_API_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_API_KEY)
    except Exception:
        supabase = None

EVENTS: list[dict] = []

# Dynamic pricing tiers loaded from RETRY_PRICE_TIERS
def _load_price_tiers() -> list[int]:
    tiers = os.getenv("RETRY_PRICE_TIERS", "480,720,980")
    try:
        values = [int(t.strip()) for t in tiers.split(",") if t.strip()]
    except ValueError:
        values = [480, 720, 980]
    return [0] + values

PRICES = _load_price_tiers()
PRO_PRICE_MONTHLY = int(os.getenv("PRO_PRICE_MONTHLY", "980"))

PRICE_VARIANTS = [480, 720, 980]

# Reward ad configuration
AD_REWARD_POINTS = int(os.getenv("AD_REWARD_POINTS", "1"))
RETRY_POINT_COST = int(os.getenv("RETRY_POINT_COST", "5"))

# Load normative distribution for percentile scores
_dist_path = os.path.join(
    os.path.dirname(__file__), "data", "normative_distribution.json"
)
with open(_dist_path) as f:
    NORMATIVE_DIST = json.load(f)

# Load political survey items
_survey_path = os.path.join(os.path.dirname(__file__), "data", "political_survey.json")
with open(_survey_path) as f:
    _survey_data = json.load(f)
    POLITICAL_SURVEY = _survey_data.get("questions", [])
    PARTIES = _survey_data.get("parties", [])


class OTPRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None


class OTPVerify(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    code: str


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]


class QuizStartResponse(BaseModel):
    session_id: str
    questions: List[QuizQuestion]


class QuizAnswer(BaseModel):
    id: int
    answer: int


class QuizSubmitRequest(BaseModel):
    answers: List[QuizAnswer]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class AdaptiveStartResponse(BaseModel):
    session_id: str
    question: QuizQuestion


class AdaptiveAnswerRequest(BaseModel):
    session_id: str
    answer: int


class AdaptiveAnswerResponse(BaseModel):
    finished: bool
    next_question: Optional[QuizQuestion] = None
    score: Optional[float] = None
    percentile: Optional[float] = None


class SurveyItem(BaseModel):
    id: int
    statement: str


class PartyItem(BaseModel):
    id: int
    name: str


class SurveyStartResponse(BaseModel):
    items: List[SurveyItem]
    parties: List[PartyItem]


class SurveyAnswer(BaseModel):
    id: int
    value: int


class SurveySubmitRequest(BaseModel):
    answers: List[SurveyAnswer]


class PartySelection(BaseModel):
    user_id: str
    party_ids: List[int]


class DemographicInfo(BaseModel):
    user_id: str
    age_band: str
    gender: str
    income_band: str
    occupation: str


class SurveyResult(BaseModel):
    left_right: float
    libertarian_authoritarian: float
    category: str
    description: str


class PricingResponse(BaseModel):
    price: int
    retry_price: int
    plays: int
    processor: str
    pro_price: int
    variant: int


class UserStats(BaseModel):
    plays: int
    referrals: int
    scores: list
    party_log: list


class UserAction(BaseModel):
    user_id: str


class QuestionUpload(BaseModel):
    questions: list


def hash_phone(phone: str, salt: str) -> str:
    return hmac.new(salt.encode(), phone.encode(), hashlib.sha256).hexdigest()


# Adaptive testing session store
OTP_CODES = {}


@app.post("/auth/request-otp")
async def request_otp(data: OTPRequest):
    if data.phone:
        code = str(random.randint(100000, 999999))
        send_otp(data.phone, code)
        OTP_CODES[data.phone] = code
        return {"status": "sent"}
    if data.email:
        supabase.auth.sign_in_with_otp({"email": data.email})
        return {"status": "email_sent"}
    raise HTTPException(status_code=400, detail="No contact provided")


@app.post("/auth/verify-otp")
async def verify_otp(data: OTPVerify):
    if data.phone:
        if OTP_CODES.get(data.phone) != data.code:
            raise HTTPException(status_code=400, detail="Invalid code")
        OTP_CODES.pop(data.phone, None)
    elif data.email:
        user = supabase.auth.verify_otp(
            {"email": data.email, "token": data.code, "type": "email"}
        )
        if not user:
            raise HTTPException(status_code=400, detail="Invalid code")
    else:
        raise HTTPException(status_code=400, detail="Invalid contact")
    # store hashed phone with per-record salt and initialize counters
    phone_or_email = data.phone or data.email
    salt = secrets.token_hex(8)
    hashed = hash_phone(phone_or_email, salt)
    async with AsyncSessionLocal() as session:
        user = await session.get(User, hashed)
        if not user:
            user = User(
                hashed_id=hashed,
                salt=salt,
                plays=0,
                referrals=0,
                points=0,
                scores=[],
                party_log=[],
                party_ids=[],
                demographics={},
            )
            session.add(user)
        await session.commit()
    return {"status": "verified", "id": hashed}


def _retry_price(user: User) -> int:
    plays_paid = max((user.plays or 0) - (user.referrals or 0), 0)
    idx = plays_paid if plays_paid < len(PRICES) else len(PRICES) - 1
    return PRICES[idx]


def _assign_variant(user: User) -> int:
    if user.variant is None:
        user.variant = random.randint(0, len(PRICE_VARIANTS) - 1)
    return user.variant


@app.get("/pricing/{user_id}", response_model=PricingResponse)
async def pricing(user_id: str, region: str = "US"):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(hashed_id=user_id, salt="", plays=0, referrals=0, points=0)
            session.add(user)
        processor = select_processor(region)
        variant_idx = _assign_variant(user)
        log_event({"event": "pricing_shown", "user_id": user_id, "variant": variant_idx})
        price = PRICE_VARIANTS[variant_idx]
        retry_price = _retry_price(user)
        await session.commit()
    return {
        "price": price,
        "retry_price": retry_price,
        "plays": user.plays,
        "processor": processor,
        "pro_price": PRO_PRICE_MONTHLY,
        "variant": variant_idx,
    }


@app.post("/play/record")
async def record_play(action: UserAction):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, action.user_id)
        if not user:
            user = User(hashed_id=action.user_id, salt="", plays=0, referrals=0, points=0)
            session.add(user)
        paid = False
        if user.plays >= MAX_FREE_ATTEMPTS:
            if user.points >= RETRY_POINT_COST:
                user.points -= RETRY_POINT_COST
                paid = True
            else:
                raise HTTPException(status_code=402, detail="Payment required")
        user.plays = (user.plays or 0) + 1
        await session.commit()
    log_event({"event": "play_record", "user_id": action.user_id, "paid": paid})
    return {"plays": user.plays, "points": user.points}


@app.post("/referral")
async def referral(action: UserAction):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, action.user_id)
        if not user:
            user = User(hashed_id=action.user_id, salt="", plays=0, referrals=0, points=0)
            session.add(user)
        user.referrals = (user.referrals or 0) + 1
        await session.commit()
    return {"referrals": user.referrals}


@app.post("/ads/start")
async def ads_start(action: UserAction):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, action.user_id)
        if not user:
            user = User(hashed_id=action.user_id, salt="", plays=0, referrals=0, points=0)
            session.add(user)
        await session.commit()
    log_event({"event": "ad_start", "user_id": action.user_id})
    return {"status": "started"}


@app.post("/ads/complete")
async def ads_complete(action: UserAction):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, action.user_id)
        if not user:
            user = User(hashed_id=action.user_id, salt="", plays=0, referrals=0, points=0)
            session.add(user)
        user.points = (user.points or 0) + AD_REWARD_POINTS
        await session.commit()
    log_event({"event": "ad_complete", "user_id": action.user_id})
    return {"points": user.points}


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.get("/share-image/{user_id}")
async def share_image(user_id: str, iq: float, percentile: float):
    """Generate and return a shareable result image URL."""
    url = generate_share_image(user_id, iq, percentile)
    return {"url": url}


@app.get("/quiz/sets")
async def quiz_sets():
    """Return available question set IDs."""
    return {"sets": available_sets()}


@app.get("/quiz/start", response_model=QuizStartResponse)
async def start_quiz(set_id: str | None = None):
    """Begin a fixed-form quiz.

    If ``set_id`` is provided, questions are drawn from that set;
    otherwise the global pool is used.
    """
    try:
        questions = get_random_questions(NUM_QUESTIONS, set_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    session_id = secrets.token_hex(8)
    app.state.sessions[session_id] = {"question_ids": [q["id"] for q in questions]}
    models = [
        QuizQuestion(id=q["id"], question=q["question"], options=q["options"])
        for q in questions
    ]
    return {"session_id": session_id, "questions": models}


@app.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmitRequest):
    if not payload.session_id or payload.session_id not in app.state.sessions:
        raise HTTPException(status_code=400, detail="Invalid session")
    question_ids = app.state.sessions[payload.session_id]["question_ids"]
    if len(payload.answers) != len(question_ids):
        raise HTTPException(status_code=400, detail="Expected all answers")

    responses = []
    for item in payload.answers:
        q = QUESTION_MAP.get(item.id)
        if not q or item.id not in question_ids:
            continue
        correct = item.answer == q["answer"]
        responses.append(
            {
                "a": q["irt"]["a"],
                "b": q["irt"]["b"],
                "correct": correct,
            }
        )

    theta = estimate_theta(responses)
    iq = iq_score(theta)
    pct = percentile(theta, NORMATIVE_DIST)
    ability = ability_summary(theta)
    se = standard_error(theta, responses)

    share_url = generate_share_image(payload.user_id or "anon", iq, pct)

    if payload.user_id:
        async with AsyncSessionLocal() as session:
            user = await session.get(User, payload.user_id)
            if user:
                user.plays = (user.plays or 0) + 1
                scores = user.scores or []
                scores.append({"iq": iq, "percentile": pct})
                user.scores = scores
                await session.commit()

    # remove session once quiz is graded
    app.state.sessions.pop(payload.session_id, None)

    return {
        "theta": theta,
        "iq": iq,
        "percentile": pct,
        "ability": ability,
        "se": se,
        "share_url": share_url,
    }


def _to_model(q) -> QuizQuestion:
    return QuizQuestion(id=q["id"], question=q["question"], options=q["options"])


@app.get("/adaptive/start", response_model=AdaptiveStartResponse)
async def adaptive_start(set_id: str | None = None):
    """Begin an adaptive quiz session."""
    theta = 0.0
    session_id = secrets.token_hex(8)
    questions = get_random_questions(NUM_QUESTIONS, set_id)
    question = select_next_question(theta, [], questions)
    app.state.sessions[session_id] = {
        "theta": theta,
        "asked": [question["id"]],
        "answers": [],
        "pool": questions,
    }
    return {"session_id": session_id, "question": _to_model(question)}


@app.post("/adaptive/answer", response_model=AdaptiveAnswerResponse)
async def adaptive_answer(payload: AdaptiveAnswerRequest):
    session = app.state.sessions.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    qid = session["asked"][-1]
    question = QUESTION_MAP.get(qid)
    if not question:
        raise HTTPException(status_code=400, detail="Question not found")
    correct = payload.answer == question["answer"]
    old_theta = session["theta"]
    session["theta"] = update_theta(
        old_theta, question["irt"]["a"], question["irt"]["b"], correct
    )
    session["answers"].append(
        {
            "id": qid,
            "a": question["irt"]["a"],
            "b": question["irt"]["b"],
            "correct": correct,
        }
    )

    if should_stop(session["theta"], session["answers"]):
        theta = estimate_theta(session["answers"])
        iq_val = iq_score(theta)
        pct = percentile(theta, NORMATIVE_DIST)
        ability = ability_summary(theta)
        se = standard_error(theta, session["answers"])
        share_url = generate_share_image(payload.session_id, iq_val, pct)
        del app.state.sessions[payload.session_id]
        return {
            "finished": True,
            "score": iq_val,
            "percentile": pct,
            "ability": ability,
            "se": se,
            "share_url": share_url,
        }

    next_q = select_next_question(session["theta"], session["asked"], session["pool"])
    if next_q is None:
        theta = estimate_theta(session["answers"])
        iq_val = iq_score(theta)
        pct = percentile(theta, NORMATIVE_DIST)
        ability = ability_summary(theta)
        se = standard_error(theta, session["answers"])
        share_url = generate_share_image(payload.session_id, iq_val, pct)
        del app.state.sessions[payload.session_id]
        return {
            "finished": True,
            "score": iq_val,
            "percentile": pct,
            "ability": ability,
            "se": se,
            "share_url": share_url,
        }
    session["asked"].append(next_q["id"])
    return {"finished": False, "next_question": _to_model(next_q)}


@app.get("/survey/start", response_model=SurveyStartResponse)
async def survey_start():
    items = [SurveyItem(id=i["id"], statement=i["statement"]) for i in POLITICAL_SURVEY]
    parties = [PartyItem(id=p["id"], name=p["name"]) for p in PARTIES]
    return {"items": items, "parties": parties}


@app.post("/survey/submit", response_model=SurveyResult)
async def survey_submit(payload: SurveySubmitRequest):
    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers provided")
    lr_score = 0.0
    auth_score = 0.0
    for ans in payload.answers:
        if ans.id >= len(POLITICAL_SURVEY) or ans.id < 0:
            raise HTTPException(status_code=400, detail=f"Invalid question id {ans.id}")
        item = POLITICAL_SURVEY[ans.id]
        weight = ans.value - 3  # center Likert 1-5 at 0
        lr_score += weight * item.get("lr", 0)
        auth_score += weight * item.get("auth", 0)

    # Normalize by number of items
    n = len(POLITICAL_SURVEY)
    lr_score /= n
    auth_score /= n

    if lr_score > 0.3:
        category = "Conservative"
    elif lr_score < -0.3:
        category = "Progressive"
    else:
        category = "Centrist"

    description = (
        f"Your economic views lean {'right' if lr_score > 0 else 'left'} and you are "
        f"{'authoritarian' if auth_score > 0 else 'libertarian'} leaning."
    )

    return {
        "left_right": lr_score,
        "libertarian_authoritarian": auth_score,
        "category": category,
        "description": description,
    }


@app.post("/user/demographics")
async def user_demographics(info: DemographicInfo):
    """Collect demographic information and store securely."""
    await collect_demographics(
        info.age_band,
        info.gender,
        info.income_band,
        info.occupation,
        info.user_id,
    )
    return {"status": "ok"}


@app.post("/user/party")
async def user_party(selection: PartySelection):
    """Record user's supported parties. Allows multiple selections."""
    if not selection.party_ids:
        raise HTTPException(status_code=400, detail="No party selected")
    try:
        await update_party_affiliation(selection.user_id, selection.party_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}


@app.get("/user/stats/{user_id}", response_model=UserStats)
async def user_stats(user_id: str):
    """Return play counts and history for a user."""
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "plays": user.plays or 0,
            "referrals": user.referrals or 0,
            "scores": user.scores or [],
            "party_log": user.party_log or [],
        }


@app.get("/points/{user_id}")
async def points_balance(user_id: str):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"points": user.points or 0}


@app.post("/analytics")
async def analytics(event: dict):
    """Log client-side events to self-hosted analytics."""
    import logging
    logging.getLogger(__name__).info("Event: %s", event)
    log_event(event)
    EVENTS.append(event)
    return {}


@app.get("/leaderboard")
async def leaderboard():
    """Return party IQ leaderboard with differential privacy noise."""
    epsilon = float(os.getenv("DP_EPSILON", "1.0"))
    data = await leaderboard_by_party(epsilon)
    return {"leaderboard": data}


@app.get("/data/iq")
async def dp_data_api(
    api_key: str,
    party_id: int | None = None,
    age_band: str | None = None,
    gender: str | None = None,
    income_band: str | None = None,
):
    """Return aggregated IQ stats for paying clients with differential privacy."""

    if api_key != os.getenv("DATA_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Invalid API key")

    epsilon = float(os.getenv("DP_EPSILON", "1.0"))
    scores: List[float] = []
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    for user in users:
        demo = user.demographics or {}
        if age_band and demo.get("age_band") != age_band:
            continue
        if gender and demo.get("gender") != gender:
            continue
        if income_band and demo.get("income_band") != income_band:
            continue
        if party_id is not None and party_id not in (user.party_ids or []):
            continue
        for s in (user.scores or []):
            scores.append(s.get("iq"))

    if len(scores) < MIN_BUCKET_SIZE:
        raise HTTPException(status_code=400, detail="Not enough data")

    mean = dp_average(scores, epsilon, min_count=MIN_BUCKET_SIZE)
    if mean is None:
        raise HTTPException(status_code=400, detail="Not enough data")

    return {"count": len(scores), "avg_iq": mean}


@app.post("/admin/update-norms")
async def admin_update_norms(api_key: str):
    """Update normative distribution from stored user scores."""
    if api_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Invalid API key")

    scores: List[float] = []
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    for user in users:
        for s in (user.scores or []):
            scores.append(s.get("iq"))
    update_normative_distribution(scores)
    return {"added": len(scores)}


@app.get("/admin/dif-report")
async def admin_dif_report(api_key: str):
    """Return DIF report for question bias analysis."""
    if api_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=403, detail="Invalid API key")
    path = os.getenv("DIF_DATA_FILE", "data/responses.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No data")
    report = dif_report(path)
    return {"dif": report}


@app.post("/admin/upload-questions")
async def admin_upload_questions(payload: QuestionUpload, x_admin_api_key: str = Header(...)):
    """Import a list of questions using the CLI helper."""
    if x_admin_api_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not isinstance(payload.questions, list):
        raise HTTPException(status_code=400, detail="Field 'questions' must be a list of objects")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "upload.json"
        tmp_path.write_text(json.dumps(payload.questions, ensure_ascii=False), encoding="utf-8")

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            try:
                import_dir(Path(tmpdir))
            except Exception as e:
                raise HTTPException(status_code=422, detail=str(e))
        log = f.getvalue().strip()

    return {"status": "success", "log": log}


@app.get("/admin/question-bank-info")
async def admin_question_bank_info(x_admin_api_key: str = Header(...)):
    """Return metadata about the current question bank."""
    if x_admin_api_key != os.getenv("ADMIN_API_KEY", ""):
        raise HTTPException(status_code=401, detail="Invalid API key")
    bank_path = Path(__file__).resolve().parent / "data" / "question_bank.json"
    try:
        with bank_path.open() as f:
            data = json.load(f)
        return {"count": len(data)}
    except FileNotFoundError:
        return {"count": 0}
