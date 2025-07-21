import os
import hashlib
import hmac
import secrets
import random
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "twilio")
if SMS_PROVIDER == "twilio":
    from twilio.rest import Client as TwilioClient
elif SMS_PROVIDER == "sns":
    import boto3
else:
    raise RuntimeError("Unsupported SMS provider")

from .questions import DEFAULT_QUESTIONS
from .irt import update_theta, percentile
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

# SMS provider setup
if SMS_PROVIDER == "twilio":
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_VERIFY_SID = os.environ.get("TWILIO_VERIFY_SERVICE_SID", "")
    sms_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
elif SMS_PROVIDER == "sns":
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    sms_client = boto3.client("sns", region_name=AWS_REGION)
else:
    sms_client = None

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


class PricingResponse(BaseModel):
    price: int
    plays: int


class UserAction(BaseModel):
    user_id: str


def hash_phone(phone: str, salt: str) -> str:
    return hmac.new(salt.encode(), phone.encode(), hashlib.sha256).hexdigest()


# Adaptive testing session store
SESSIONS = {}
OTP_CODES = {}


@app.post("/auth/request-otp")
async def request_otp(data: OTPRequest):
    if data.phone and SMS_PROVIDER == "twilio":
        verification = sms_client.verify.v2.services(
            TWILIO_VERIFY_SID
        ).verifications.create(to=data.phone, channel="sms")
        return {"status": verification.status}
    if data.phone and SMS_PROVIDER == "sns":
        code = str(random.randint(100000, 999999))
        sms_client.publish(PhoneNumber=data.phone, Message=f"Your code is {code}")
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
    if data.phone and SMS_PROVIDER == "twilio":
        check = sms_client.verify.v2.services(
            TWILIO_VERIFY_SID
        ).verification_checks.create(to=data.phone, code=data.code)
        if check.status != "approved":
            raise HTTPException(status_code=400, detail="Invalid code")
    elif data.phone and SMS_PROVIDER == "sns":
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
async def pricing(user_id: str):
    user = USERS.get(user_id)
    if not user:
        return {"price": PRICES[0], "plays": 0}
    price = _current_price(user)
    return {"price": price, "plays": user.get("plays", 0)}


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
    score = 0
    for item in payload.answers:
        try:
            correct = DEFAULT_QUESTIONS[item.id]["answer"]
        except IndexError:
            continue
        if item.answer == correct:
            score += 1
    if payload.user_id and payload.user_id in USERS:
        USERS[payload.user_id]["plays"] = USERS[payload.user_id].get("plays", 0) + 1
    return {"score": score}


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
        score = session["theta"]
        pct = percentile(score, NORMATIVE_DIST)
        del SESSIONS[payload.session_id]
        return {"finished": True, "score": score, "percentile": pct}

    next_q = _select_question(session["theta"], session["asked"])
    if next_q is None:
        score = session["theta"]
        pct = percentile(score, NORMATIVE_DIST)
        del SESSIONS[payload.session_id]
        return {"finished": True, "score": score, "percentile": pct}
    session["asked"].append(next_q["id"])
    return {"finished": False, "next_question": _to_model(next_q)}
