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

from .questions import DEFAULT_QUESTIONS
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

# TODO: initialize Supabase client here when available

# In-memory placeholder for user records
# {hashed_id: {"salt": str, "plays": int, "referrals": int}}
USERS = {}

# Dynamic pricing tiers: first play free then increasing prices
PRICES = [0, 480, 720, 980]

# Load normative distribution for percentile scores
_dist_path = os.path.join(
    os.path.dirname(__file__), "data", "normative_distribution.json"
)
with open(_dist_path) as f:
    NORMATIVE_DIST = json.load(f)

# Load political survey items
_survey_path = os.path.join(os.path.dirname(__file__), "data", "political_survey.json")
with open(_survey_path) as f:
    POLITICAL_SURVEY = json.load(f)


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
    questions: List[QuizQuestion]


class QuizAnswer(BaseModel):
    id: int
    answer: int


class QuizSubmitRequest(BaseModel):
    answers: List[QuizAnswer]
    user_id: Optional[str] = None


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


class SurveyStartResponse(BaseModel):
    items: List[SurveyItem]


class SurveyAnswer(BaseModel):
    id: int
    value: int


class SurveySubmitRequest(BaseModel):
    answers: List[SurveyAnswer]


class SurveyResult(BaseModel):
    left_right: float
    libertarian_authoritarian: float
    category: str
    description: str


class PricingResponse(BaseModel):
    price: int
    plays: int
    processor: str


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
        USERS[hashed] = {"salt": salt, "plays": 0, "referrals": 0}
    # TODO: save hashed phone and salt to database with user record
    return {"status": "verified", "id": hashed}


def _current_price(user) -> int:
    plays_paid = max(user.get("plays", 0) - user.get("referrals", 0), 0)
    idx = plays_paid if plays_paid < len(PRICES) else len(PRICES) - 1
    return PRICES[idx]


@app.get("/pricing/{user_id}", response_model=PricingResponse)
async def pricing(user_id: str, region: str = "US"):
    user = USERS.get(user_id)
    if not user:
        processor = select_processor(region)
        return {"price": PRICES[0], "plays": 0, "processor": processor}
    price = _current_price(user)
    processor = select_processor(region)
    return {"price": price, "plays": user.get("plays", 0), "processor": processor}


@app.post("/play/record")
async def record_play(action: UserAction):
    user = USERS.setdefault(action.user_id, {"salt": "", "plays": 0, "referrals": 0})
    user["plays"] = user.get("plays", 0) + 1
    return {"plays": user["plays"]}


@app.post("/referral")
async def referral(action: UserAction):
    user = USERS.setdefault(action.user_id, {"salt": "", "plays": 0, "referrals": 0})
    user["referrals"] = user.get("referrals", 0) + 1
    return {"referrals": user["referrals"]}


@app.get("/ping")
async def ping():
    return {"message": "pong"}


@app.get("/quiz/start", response_model=QuizStartResponse)
async def start_quiz():
    sample = random.sample(list(enumerate(DEFAULT_QUESTIONS)), k=20)
    questions = [
        QuizQuestion(id=idx, question=q["question"], options=q["options"])
        for idx, q in sample
    ]
    return {"questions": questions}


@app.post("/quiz/submit")
async def submit_quiz(payload: QuizSubmitRequest):
    if len(payload.answers) != 20:
        raise HTTPException(status_code=400, detail="Expected 20 answers")

    responses = []
    for item in payload.answers:
        try:
            q = DEFAULT_QUESTIONS[item.id]
        except IndexError:
            continue
        correct = item.answer == q["answer"]
        responses.append({
            "a": q["irt"]["a"],
            "b": q["irt"]["b"],
            "correct": correct,
        })

    theta = estimate_theta(responses)
    iq = iq_score(theta)
    pct = percentile(theta, NORMATIVE_DIST)
    ability = ability_summary(theta)

    if payload.user_id and payload.user_id in USERS:
        USERS[payload.user_id]["plays"] = USERS[payload.user_id].get("plays", 0) + 1

    return {"theta": theta, "iq": iq, "percentile": pct, "ability": ability}


def _select_question(theta: float, asked: List[int]):
    remaining = [q for q in DEFAULT_QUESTIONS if q["id"] not in asked]
    if not remaining:
        return None
    return min(remaining, key=lambda q: abs(q["irt"]["b"] - theta))


def _to_model(q) -> QuizQuestion:
    return QuizQuestion(id=q["id"], question=q["question"], options=q["options"])


@app.get("/adaptive/start", response_model=AdaptiveStartResponse)
async def adaptive_start():
    theta = 0.0
    session_id = secrets.token_hex(8)
    question = _select_question(theta, [])
    SESSIONS[session_id] = {"theta": theta, "asked": [question["id"]], "answers": []}
    return {"session_id": session_id, "question": _to_model(question)}


@app.post("/adaptive/answer", response_model=AdaptiveAnswerResponse)
async def adaptive_answer(payload: AdaptiveAnswerRequest):
    session = SESSIONS.get(payload.session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    qid = session["asked"][-1]
    question = next(q for q in DEFAULT_QUESTIONS if q["id"] == qid)
    correct = payload.answer == question["answer"]
    old_theta = session["theta"]
    session["theta"] = update_theta(
        old_theta, question["irt"]["a"], question["irt"]["b"], correct
    )
    session["answers"].append({"id": qid, "answer": payload.answer, "correct": correct})

    if len(session["answers"]) >= 20 or (
        len(session["answers"]) >= 5 and abs(session["theta"] - old_theta) < 0.05
    ):
        theta = estimate_theta([
            {"a": DEFAULT_QUESTIONS[a["id"]]["irt"]["a"],
             "b": DEFAULT_QUESTIONS[a["id"]]["irt"]["b"],
             "correct": a["correct"]}
            for a in session["answers"]
        ])
        iq_val = iq_score(theta)
        pct = percentile(theta, NORMATIVE_DIST)
        ability = ability_summary(theta)
        del SESSIONS[payload.session_id]
        return {"finished": True, "score": iq_val, "percentile": pct, "ability": ability}

    next_q = _select_question(session["theta"], session["asked"])
    if next_q is None:
        theta = estimate_theta([
            {"a": DEFAULT_QUESTIONS[a["id"]]["irt"]["a"],
             "b": DEFAULT_QUESTIONS[a["id"]]["irt"]["b"],
             "correct": a["correct"]}
            for a in session["answers"]
        ])
        iq_val = iq_score(theta)
        pct = percentile(theta, NORMATIVE_DIST)
        ability = ability_summary(theta)
        del SESSIONS[payload.session_id]
        return {"finished": True, "score": iq_val, "percentile": pct, "ability": ability}
    session["asked"].append(next_q["id"])
    return {"finished": False, "next_question": _to_model(next_q)}


@app.get("/survey/start", response_model=SurveyStartResponse)
async def survey_start():
    items = [SurveyItem(id=i["id"], statement=i["statement"]) for i in POLITICAL_SURVEY]
    return {"items": items}


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


@app.post("/analytics")
async def analytics(event: dict):
    """Log client-side events to self-hosted analytics."""
    app.logger.info("Event: %s", event)
    return {}
