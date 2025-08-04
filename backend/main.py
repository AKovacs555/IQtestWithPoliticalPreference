import os
import hashlib
import hmac
import secrets
import random
import time
from datetime import datetime
from typing import List, Optional

import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    get_balanced_random_questions,
    get_balanced_random_questions_by_set,
    get_balanced_random_questions_global,
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
from payment import (
    select_processor,
    create_nowpayments_invoice,
    get_nowpayments_status,
)
from analytics import log_event
from tools.dif_analysis import dif_report
from routes.exam import router as exam_router
from routes.admin_questions import router as admin_questions_router
from routes.admin_import_questions import router as admin_import_router
from routes.admin_surveys import router as admin_surveys_router
from routes.admin_users import router as admin_users_router
from routes.quiz import router as quiz_router
from routes.user import router as user_router
import json

app = FastAPI()
app.state.sessions = {}

# CORS for SPA
frontend_origins = os.getenv("FRONTEND_ORIGINS", "").split(",")
frontend_origins = [o.strip() for o in frontend_origins if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(exam_router)

# Admin routers
app.include_router(admin_questions_router)
app.include_router(admin_import_router)
app.include_router(admin_surveys_router)
app.include_router(admin_users_router)

# Public routers
app.include_router(quiz_router)
app.include_router(user_router)

# SMS provider handled by sms_service module

# Number of questions per quiz session
NUM_QUESTIONS = int(os.getenv("NUM_QUESTIONS", "20"))

# Maximum free attempts before payment is required
MAX_FREE_ATTEMPTS = int(os.getenv("MAX_FREE_ATTEMPTS", "1"))

from db import (
    get_user,
    create_user as db_create_user,
    update_user as db_update_user,
    get_all_users,
    get_supabase,
    get_surveys,
    get_parties,
    insert_survey_answers,
    get_survey_answers,
    insert_survey_responses,
    get_answered_survey_ids,
)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY", "")

if not SUPABASE_URL or not SUPABASE_API_KEY:
    logger.warning("SUPABASE_URL or SUPABASE_API_KEY is not configured")

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
    image: Optional[str] = None


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
    id: str
    statement: str
    options: list[str]
    type: str
    exclusive_options: list[int] = []


class PartyItem(BaseModel):
    id: int
    name: str


class SurveyStartResponse(BaseModel):
    items: List[SurveyItem]
    parties: List[PartyItem]


class SurveyAnswer(BaseModel):
    id: str
    selections: List[int]


class SurveySubmitRequest(BaseModel):
    answers: List[SurveyAnswer]
    user_id: Optional[str] = None


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
    free_attempts: int
    processor: str
    pro_price: int
    variant: int


class ScoreEntry(BaseModel):
    iq: float
    percentile: float
    timestamp: str | None = None
    set_id: str | None = None


class UserStats(BaseModel):
    plays: int
    referrals: int
    scores: list[ScoreEntry]
    party_log: list
    free_attempts: int


class HistoryResponse(BaseModel):
    scores: list[ScoreEntry]


class UserAction(BaseModel):
    user_id: str


class PurchaseRequest(BaseModel):
    user_id: str
    amount: int
    pay_currency: str | None = None



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
        supabase = get_supabase()
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
        supabase = get_supabase()
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
    user = get_user(hashed)
    if not user:
        db_create_user(
            {
                "hashed_id": hashed,
                "salt": salt,
                "plays": 0,
                "referrals": 0,
                "points": 0,
                "scores": [],
                "party_log": [],
                "demographic": {},
            }
        )
    return {"status": "verified", "id": hashed}


def _retry_price(user: dict) -> int:
    plays_paid = max((user.get("plays", 0)) - (user.get("referrals", 0)), 0)
    idx = plays_paid if plays_paid < len(PRICES) else len(PRICES) - 1
    return PRICES[idx]


def _assign_variant(user: dict) -> int:
    """Return a stable variant index for the user."""
    return abs(hash(user["hashed_id"])) % len(PRICE_VARIANTS)


@app.get("/pricing/{user_id}", response_model=PricingResponse)
async def pricing(user_id: str, region: str = "US"):
    user = get_user(user_id)
    if not user:
        user = db_create_user(
            {
                "hashed_id": user_id,
                "salt": "",
                "plays": 0,
                "referrals": 0,
                "points": 0,
                "scores": [],
                "party_log": [],
                "demographic": {},
                "free_attempts": MAX_FREE_ATTEMPTS,
            }
        )
    elif "free_attempts" not in user:
        user["free_attempts"] = MAX_FREE_ATTEMPTS
        db_update_user(user_id, {"free_attempts": MAX_FREE_ATTEMPTS})
    processor = select_processor(region)
    variant_idx = _assign_variant(user)
    log_event({"event": "pricing_shown", "user_id": user_id, "variant": variant_idx})
    price = PRICE_VARIANTS[variant_idx]
    retry_price = _retry_price(user)
    return {
        "price": price,
        "retry_price": retry_price,
        "plays": user.get("plays", 0),
        "free_attempts": user.get("free_attempts", MAX_FREE_ATTEMPTS),
        "processor": processor,
        "pro_price": PRO_PRICE_MONTHLY,
        "variant": variant_idx,
    }


@app.post("/purchase")
async def purchase(payload: PurchaseRequest, region: str = "US"):
    processor = select_processor(region)
    if processor == "nowpayments":
        invoice = create_nowpayments_invoice(
            str(payload.amount),
            os.getenv("NOWPAYMENTS_CURRENCY", "USD"),
            payload.pay_currency,
            payload.user_id,
        )
        return {
            "processor": processor,
            "payment_url": invoice.get("invoice_url") or invoice.get("payment_url"),
            "payment_id": invoice.get("payment_id"),
        }
    raise HTTPException(status_code=400, detail="Payment processor not configured")


@app.post("/payment/nowpayments/callback")
async def nowpayments_callback(payment_id: str):
    data = get_nowpayments_status(payment_id)
    if data.get("payment_status") == "finished":
        log_event({"event": "nowpayments_finished", "payment_id": payment_id})
    return {"status": "ok"}


@app.post("/play/record")
async def record_play(action: UserAction):
    user = get_user(action.user_id)
    if not user:
        user = db_create_user(
            {
                "hashed_id": action.user_id,
                "salt": "",
                "plays": 0,
                "referrals": 0,
                "points": 0,
                "scores": [],
                "party_log": [],
                "demographic": {},
                "free_attempts": MAX_FREE_ATTEMPTS,
            }
        )
    paid = False
    if user.get("free_attempts", MAX_FREE_ATTEMPTS) > 0:
        user["free_attempts"] = user.get("free_attempts", MAX_FREE_ATTEMPTS) - 1
    else:
        if user.get("points", 0) >= RETRY_POINT_COST:
            user["points"] -= RETRY_POINT_COST
            paid = True
        else:
            raise HTTPException(status_code=402, detail="Payment required")
    user["plays"] = user.get("plays", 0) + 1
    db_update_user(action.user_id, {
        "plays": user["plays"],
        "points": user.get("points", 0),
        "free_attempts": user.get("free_attempts", 0),
    })
    log_event({"event": "play_record", "user_id": action.user_id, "paid": paid})
    return {"plays": user["plays"], "points": user.get("points", 0), "free_attempts": user.get("free_attempts", 0)}


@app.post("/referral")
async def referral(action: UserAction):
    user = get_user(action.user_id)
    if not user:
        user = db_create_user(
            {
                "hashed_id": action.user_id,
                "salt": "",
                "plays": 0,
                "referrals": 0,
                "points": 0,
                "scores": [],
                "party_log": [],
                "demographic": {},
            }
        )
    user["referrals"] = user.get("referrals", 0) + 1
    db_update_user(action.user_id, {"referrals": user["referrals"]})
    return {"referrals": user["referrals"]}


@app.post("/ads/start")
async def ads_start(action: UserAction):
    user = get_user(action.user_id)
    if not user:
        user = db_create_user(
            {
                "hashed_id": action.user_id,
                "salt": "",
                "plays": 0,
                "referrals": 0,
                "points": 0,
                "scores": [],
                "party_log": [],
                "demographic": {},
            }
        )
    log_event({"event": "ad_start", "user_id": action.user_id})
    return {"status": "started"}


@app.post("/ads/complete")
async def ads_complete(action: UserAction):
    user = get_user(action.user_id)
    if not user:
        user = db_create_user(
            {
                "hashed_id": action.user_id,
                "salt": "",
                "plays": 0,
                "referrals": 0,
                "points": 0,
                "scores": [],
                "party_log": [],
                "demographic": {},
            }
        )
    user["points"] = user.get("points", 0) + AD_REWARD_POINTS
    db_update_user(action.user_id, {"points": user["points"]})
    log_event({"event": "ad_complete", "user_id": action.user_id})
    return {"points": user["points"]}


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.get("/share-image/{user_id}")
async def share_image(user_id: str, iq: float, percentile: float):
    """Generate and return a shareable result image URL."""
    url = generate_share_image(user_id, iq, percentile)
    return {"url": url}




def _to_model(q) -> QuizQuestion:
    return QuizQuestion(
        id=q["id"],
        question=q["question"],
        options=q["options"],
        image=q.get("image"),
    )


@app.get("/adaptive/start", response_model=AdaptiveStartResponse)
async def adaptive_start(set_id: str | None = None, user_id: str | None = None):
    """Begin an adaptive quiz session."""
    if user_id:
        user = get_user(user_id)
        if user and not user.get("survey_completed"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "survey_required",
                    "message": "Please complete the survey before taking the IQ test.",
                },
            )
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
async def survey_start(
    lang: str = "en", user_id: str | None = None, nationality: str | None = None
):
    surveys = get_surveys(lang)
    if not surveys and lang != "en":
        surveys = get_surveys("en")
    user = get_user(user_id) if user_id else None
    user_nationality = nationality or (user.get("nationality") if user else None)
    answered_ids: set[str] = set()
    if user_id:
        answered_ids = set(get_answered_survey_ids(user_id))
    items_raw = [
        q
        for q in surveys
        if (
            q.get("group_id") not in answered_ids
            and (
                not q.get("target_countries")
                or not user_nationality
                or user_nationality in q.get("target_countries")
            )
        )
    ]
    parties_data = get_parties()
    items = [
        SurveyItem(
            id=str(i["id"]),
            statement=i["statement"],
            options=i.get("options", []),
            type=i.get("type", "sa"),
            exclusive_options=i.get("exclusive_options", []),
        )
        for i in items_raw
    ]
    parties = [PartyItem(id=p["id"], name=p["name"]) for p in parties_data]
    return {"items": items, "parties": parties}


@app.get("/surveys")
async def public_surveys(lang: str = "en"):
    return {"questions": get_surveys(lang)}


@app.post("/survey/submit", response_model=SurveyResult)
async def survey_submit(payload: SurveySubmitRequest):
    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers provided")

    questions = {str(q["id"]): q for q in get_surveys()}
    lr_score = 0.0
    auth_score = 0.0

    answer_rows: List[dict] = []
    response_rows: List[dict] = []
    for ans in payload.answers:
        item = questions.get(ans.id)
        if not item:
            raise HTTPException(status_code=400, detail=f"Invalid question id {ans.id}")

        selections = ans.selections
        if item.get("type") == "sa":
            if len(selections) != 1:
                raise HTTPException(status_code=400, detail="Exactly one option required")
            choice = selections[0]
        else:
            if not selections:
                raise HTTPException(status_code=400, detail="At least one option required")
            if any(
                idx in item.get("exclusive_options", []) and len(selections) > 1
                for idx in selections
            ):
                raise HTTPException(status_code=400, detail="Exclusive option selected with others")
            choice = selections[0]

        if choice < 0 or choice >= len(item.get("options", [])):
            raise HTTPException(status_code=400, detail=f"Invalid option index {choice}")

        weight = choice - (len(item.get("options", [])) - 1) / 2
        lr_score += weight * (item.get("lr") or 0)
        auth_score += weight * (item.get("auth") or 0)

        if payload.user_id:
            for sel in selections:
                answer_rows.append(
                    {
                        "user_id": payload.user_id,
                        "group_id": item.get("group_id"),
                        "option_index": sel,
                    }
                )
            response_rows.append(
                {
                    "user_id": payload.user_id,
                    "survey_group_id": item.get("group_id"),
                    "answer": {"id": ans.id, "selections": selections},
                }
            )

    n = len(payload.answers)
    if n:
        lr_score /= n
        auth_score /= n

    if answer_rows:
        insert_survey_answers(answer_rows)
    if response_rows:
        insert_survey_responses(response_rows)
        db_update_user(payload.user_id, {"survey_completed": True})

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


class UserAction(BaseModel):
    user_id: str


@app.post("/survey/complete")
async def survey_complete(action: UserAction):
    db_update_user(action.user_id, {"survey_completed": True})
    return {"status": "ok"}


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
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "plays": user.get("plays", 0),
        "referrals": user.get("referrals", 0),
        "scores": user.get("scores") or [],
        "party_log": user.get("party_log") or [],
        "free_attempts": user.get("free_attempts", MAX_FREE_ATTEMPTS),
    }


@app.get("/user/history/{user_id}", response_model=HistoryResponse)
async def user_history(user_id: str):
    """Return past quiz scores for the user sorted by timestamp desc."""
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    scores = user.get("scores") or []
    scores = sorted(
        scores,
        key=lambda s: s.get("timestamp") or "",
        reverse=True,
    )
    return {"scores": scores}


@app.get("/points/{user_id}")
async def points_balance(user_id: str):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"points": user.get("points", 0)}


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


@app.get("/stats/iq_histogram")
async def iq_histogram(user_id: str):
    users = get_all_users()
    top_scores = []
    user_score = None
    for u in users:
        uscores = [s.get("iq") for s in (u.get("scores") or [])]
        if not uscores:
            continue
        top = max(uscores)
        top_scores.append(top)
        if u.get("hashed_id") == user_id:
            user_score = top
    if not top_scores:
        return {
            "histogram": [],
            "bucket_edges": [],
            "user_score": user_score,
            "user_percentile": None,
        }
    min_edge = int(min(top_scores) // 5 * 5)
    max_edge = int(max(top_scores) // 5 * 5) + 5
    bucket_edges = list(range(min_edge, max_edge + 1, 5))
    hist_counts = [0] * (len(bucket_edges) - 1)
    for s in top_scores:
        idx = min(int((s - min_edge) // 5), len(hist_counts) - 1)
        hist_counts[idx] += 1
    percentile = None
    if user_score is not None:
        rank = sum(1 for s in top_scores if s <= user_score)
        percentile = rank / len(top_scores) * 100
    return {
        "histogram": hist_counts,
        "bucket_edges": bucket_edges,
        "user_score": user_score,
        "user_percentile": percentile,
    }


@app.get("/stats/survey_options/{group_id}")
async def survey_option_stats(group_id: str):
    answers = get_survey_answers(group_id)
    if not answers:
        return {"options": [], "averages": [], "counts": []}
    users = {u["hashed_id"]: u for u in get_all_users()}
    survey = next(
        (s for s in get_surveys("en") if s.get("group_id") == group_id),
        None,
    )
    if not survey:
        survey = next(
            (s for s in get_surveys() if s.get("group_id") == group_id),
            None,
        )
    options = survey.get("options", []) if survey else []
    iq_by_option: dict[int, list[float]] = {i: [] for i in range(len(options))}
    for ans in answers:
        user = users.get(ans["user_id"])
        if not user:
            continue
        uscores = [s.get("iq") for s in (user.get("scores") or [])]
        if not uscores:
            continue
        top = max(uscores)
        iq_by_option.setdefault(ans["option_index"], []).append(top)
    averages = []
    counts = []
    for i in range(len(options)):
        vals = iq_by_option.get(i, [])
        counts.append(len(vals))
        averages.append(sum(vals) / len(vals) if vals else 0)
    return {"options": options, "averages": averages, "counts": counts}


@app.get("/stats/distribution")
async def stats_distribution(user_id: str, epsilon: float = 1.0):
    """Return histogram of top IQ scores and user's percentile."""
    users = get_all_users()
    scores = []
    user_score = None
    for u in users:
        uscores = [s.get("iq") for s in (u.get("scores") or [])]
        if not uscores:
            continue
        top = max(uscores)
        scores.append(top)
        if u.get("hashed_id") == user_id:
            user_score = top

    scores.sort()
    buckets: dict[int, int] = {}
    for s in scores:
        b = int(s // 5 * 5)
        buckets[b] = buckets.get(b, 0) + 1
    histogram = [{"bin": k, "count": v} for k, v in sorted(buckets.items())]
    mean = dp_average(scores, epsilon, min_count=MIN_BUCKET_SIZE)
    percentile = None
    if user_score is not None and scores:
        rank = sum(1 for s in scores if s <= user_score)
        percentile = rank / len(scores) * 100
    party_means = await leaderboard_by_party(epsilon)
    return {
        "histogram": histogram,
        "mean": mean,
        "user_score": user_score,
        "percentile": percentile,
        "party_means": party_means,
    }


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
    users = get_all_users()
    for user in users:
        demo = user.get("demographic") or {}
        if age_band and demo.get("age_band") != age_band:
            continue
        if gender and demo.get("gender") != gender:
            continue
        if income_band and demo.get("income_band") != income_band:
            continue
        latest_parties = user.get("party_log")
        latest_parties = latest_parties[-1]["party_ids"] if latest_parties else []
        if party_id is not None and party_id not in latest_parties:
            continue
        for s in (user.get("scores") or []):
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
    users = get_all_users()
    for user in users:
        for s in (user.get("scores") or []):
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


