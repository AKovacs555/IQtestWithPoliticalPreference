import os
import hashlib
import hmac
import secrets
import random
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .sms_service import send_otp, SMS_PROVIDER
from .todo_features import (
    leaderboard_by_party,
    generate_share_image,
    update_normative_distribution,
    dp_average,
    MIN_BUCKET_SIZE,
)
from .demographics import collect_demographics
from .party import update_party_affiliation
from .dp import add_laplace

from .questions import DEFAULT_QUESTIONS, QUESTION_MAP, get_random_questions
from .irt import update_theta, percentile
from .scoring import estimate_theta, iq_score, ability_summary
from .payment import select_processor
import json

app = FastAPI()

# CORS for SPA
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SMS provider handled by sms_service module

# Database placeholder (Supabase)
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY", "")

# Number of questions per quiz session
NUM_QUESTIONS = int(os.getenv("NUM_QUESTIONS", "20"))

# Maximum free attempts before payment is required
MAX_FREE_ATTEMPTS = int(os.getenv("MAX_FREE_ATTEMPTS", "1"))

# TODO: initialize Supabase client here when available

# In-memory placeholder for user records
# {hashed_id: {"salt": str, "plays": int, "referrals": int}}
USERS = {}

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


class SurveyResult(BaseModel):
    left_right: float
    libertarian_authoritarian: float
    category: str
    description: str


class PricingResponse(BaseModel):
    price: int
    plays: int
    processor: str
    pro_price: int


class UserStats(BaseModel):
    plays: int
    referrals: int
    scores: list
    party_log: list


class UserAction(BaseModel):
    user_id: str


def hash_phone(phone: str, salt: str) -> str:
    return hmac.new(salt.encode(), phone.encode(), hashlib.sha256).hexdigest()


# Adaptive testing session store
SESSIONS = {}
OTP_CODES = {}


@app.post("/auth/request-otp")
async def request_otp(data: OTPRequest):
    if data.phone:
        code = str(random.randint(100000, 999999))
        send_otp(data.phone, code)
        OTP_CODES[data.phone] = code
        return {"status": "sent"}
    if data.email:
        from supabase import create_client

        supa = create_client(DATABASE_URL, SUPABASE_API_KEY)
        supa.auth.sign_in_with_otp({"email": data.email})
        return {"status": "email_sent"}
    raise HTTPException(status_code=400, detail="No contact provided")


@app.post("/auth/verify-otp")
async def verify_otp(data: OTPVerify):
    if data.phone:
        if OTP_CODES.get(data.phone) != data.code:
            raise HTTPException(status_code=400, detail="Invalid code")
        OTP_CODES.pop(data.phone, None)
    elif data.email:
        from supabase import create_client

        supa = create_client(DATABASE_URL, SUPABASE_API_KEY)
        user = supa.auth.verify_otp(
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
    if hashed not in USERS:
        USERS[hashed] = {
            "salt": salt,
            "plays": 0,
            "referrals": 0,
            "scores": [],
            "party_log": [],
            "demographics": {},
        }
    # TODO: save hashed phone and salt to database with user record
    return {"status": "verified", "id": hashed}


def _current_price(user) -> int:
    plays_paid = max(user.get("plays", 0) - user.get("referrals", 0), 0)
    idx = plays_paid if plays_paid < len(PRICES) else len(PRICES) - 1
    user["price_variant"] = idx
    return PRICES[idx]


@app.get("/pricing/{user_id}", response_model=PricingResponse)
async def pricing(user_id: str, region: str = "US"):
    user = USERS.setdefault(
        user_id,
        {
            "salt": "",
            "plays": 0,
            "referrals": 0,
            "scores": [],
            "party_log": [],
            "demographics": {},
        },
    )
    processor = select_processor(region)
    price = _current_price(user)
    return {
        "price": price,
        "plays": user.get("plays", 0),
        "processor": processor,
        "pro_price": PRO_PRICE_MONTHLY,
    }


@app.post("/play/record")
async def record_play(action: UserAction):
    user = USERS.setdefault(
        action.user_id,
        {
            "salt": "",
            "plays": 0,
            "referrals": 0,
            "scores": [],
            "party_log": [],
            "demographics": {},
        },
    )
    if user.get("plays", 0) >= MAX_FREE_ATTEMPTS:
        # TODO: verify payment before incrementing when paid retries are implemented
        raise HTTPException(status_code=402, detail="Payment required")
    user["plays"] = user.get("plays", 0) + 1
    return {"plays": user["plays"]}


@app.post("/referral")
async def referral(action: UserAction):
    user = USERS.setdefault(
        action.user_id,
        {
            "salt": "",
            "plays": 0,
            "referrals": 0,
            "scores": [],
            "party_log": [],
            "demographics": {},
        },
    )
    user["referrals"] = user.get("referrals", 0) + 1
    return {"referrals": user["referrals"]}


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.get("/share-image/{user_id}")
async def share_image(user_id: str, iq: float, percentile: float):
    """Generate and return a shareable result image URL."""
    url = generate_share_image(user_id, iq, percentile)
    return {"url": url}


@app.get("/quiz/start", response_model=QuizStartResponse)
async def start_quiz(question_set_id: str | None = None):
    """Begin a fixed-form quiz.

    If ``question_set_id`` is provided, questions are drawn from that set;
    otherwise the global pool is used.
    """
    questions = get_random_questions(NUM_QUESTIONS, question_set_id)
    session_id = secrets.token_hex(8)
    SESSIONS[session_id] = {"question_ids": [q["id"] for q in questions]}
    models = [
        QuizQuestion(id=q["id"], question=q["question"], options=q["options"])
        for q in questions
    ]
    return {"session_id": session_id, "questions": models}


@app.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmitRequest):
    if not payload.session_id or payload.session_id not in SESSIONS:
        raise HTTPException(status_code=400, detail="Invalid session")
    question_ids = SESSIONS[payload.session_id]["question_ids"]
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

    share_url = generate_share_image(payload.user_id or "anon", iq, pct)

    if payload.user_id and payload.user_id in USERS:
        user = USERS[payload.user_id]
        user["plays"] = user.get("plays", 0) + 1
        user.setdefault("scores", []).append({"iq": iq, "percentile": pct})

    # remove session once quiz is graded
    SESSIONS.pop(payload.session_id, None)

    return {
        "theta": theta,
        "iq": iq,
        "percentile": pct,
        "ability": ability,
        "share_url": share_url,
    }


def _select_question(theta: float, asked: List[int], pool: List[int]):
    remaining = [QUESTION_MAP[qid] for qid in pool if qid not in asked]
    if not remaining:
        return None
    return min(remaining, key=lambda q: abs(q["irt"]["b"] - theta))


def _to_model(q) -> QuizQuestion:
    return QuizQuestion(id=q["id"], question=q["question"], options=q["options"])


@app.get("/adaptive/start", response_model=AdaptiveStartResponse)
async def adaptive_start(question_set_id: str | None = None):
    """Begin an adaptive quiz session."""
    theta = 0.0
    session_id = secrets.token_hex(8)
    questions = get_random_questions(NUM_QUESTIONS, question_set_id)
    pool_ids = [q["id"] for q in questions]
    question = _select_question(theta, [], pool_ids)
    SESSIONS[session_id] = {
        "theta": theta,
        "asked": [question["id"]],
        "answers": [],
        "pool": pool_ids,
    }
    return {"session_id": session_id, "question": _to_model(question)}


@app.post("/adaptive/answer", response_model=AdaptiveAnswerResponse)
async def adaptive_answer(payload: AdaptiveAnswerRequest):
    session = SESSIONS.get(payload.session_id)
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
    session["answers"].append({"id": qid, "answer": payload.answer, "correct": correct})

    if len(session["answers"]) >= 20 or (
        len(session["answers"]) >= 5 and abs(session["theta"] - old_theta) < 0.05
    ):
        theta = estimate_theta(
            [
                {
                    "a": QUESTION_MAP[a["id"]]["irt"]["a"],
                    "b": QUESTION_MAP[a["id"]]["irt"]["b"],
                    "correct": a["correct"],
                }
                for a in session["answers"]
            ]
        )
        iq_val = iq_score(theta)
        pct = percentile(theta, NORMATIVE_DIST)
        ability = ability_summary(theta)
        share_url = generate_share_image(payload.session_id, iq_val, pct)
        del SESSIONS[payload.session_id]
        return {
            "finished": True,
            "score": iq_val,
            "percentile": pct,
            "ability": ability,
            "share_url": share_url,
        }

    next_q = _select_question(session["theta"], session["asked"], session["pool"])
    if next_q is None:
        theta = estimate_theta(
            [
                {
                    "a": QUESTION_MAP[a["id"]]["irt"]["a"],
                    "b": QUESTION_MAP[a["id"]]["irt"]["b"],
                    "correct": a["correct"],
                }
                for a in session["answers"]
            ]
        )
        iq_val = iq_score(theta)
        pct = percentile(theta, NORMATIVE_DIST)
        ability = ability_summary(theta)
        share_url = generate_share_image(payload.session_id, iq_val, pct)
        del SESSIONS[payload.session_id]
        return {
            "finished": True,
            "score": iq_val,
            "percentile": pct,
            "ability": ability,
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
    lr_score = 0.0
    auth_score = 0.0
    for ans in payload.answers:
        try:
            item = POLITICAL_SURVEY[ans.id]
        except IndexError:
            continue
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
    collect_demographics(info.age_band, info.gender, info.income_band, info.user_id)
    return {"status": "ok"}


@app.post("/user/party")
async def user_party(selection: PartySelection):
    """Record user's supported parties. Allows multiple selections."""
    try:
        update_party_affiliation(selection.user_id, selection.party_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}


@app.get("/user/stats/{user_id}", response_model=UserStats)
async def user_stats(user_id: str):
    """Return play counts and history for a user."""
    user = USERS.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "plays": user.get("plays", 0),
        "referrals": user.get("referrals", 0),
        "scores": user.get("scores", []),
        "party_log": user.get("party_log", []),
    }


@app.post("/analytics")
async def analytics(event: dict):
    """Log client-side events to self-hosted analytics."""
    app.logger.info("Event: %s", event)
    return {}


@app.get("/leaderboard")
async def leaderboard():
    """Return party IQ leaderboard with differential privacy noise."""
    epsilon = float(os.getenv("DP_EPSILON", "1.0"))
    data = leaderboard_by_party(epsilon)
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
    for user in USERS.values():
        demo = user.get("demographics", {})
        if age_band and demo.get("age_band") != age_band:
            continue
        if gender and demo.get("gender") != gender:
            continue
        if income_band and demo.get("income_band") != income_band:
            continue
        if party_id is not None and party_id not in user.get("party_ids", []):
            continue
        for s in user.get("scores", []):
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
    for user in USERS.values():
        for s in user.get("scores", []):
            scores.append(s.get("iq"))
    update_normative_distribution(scores)
    return {"added": len(scores)}
