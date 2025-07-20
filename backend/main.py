import os
import hashlib
import hmac
import secrets
import random
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from twilio.rest import Client

from .questions import DEFAULT_QUESTIONS

app = FastAPI()

# CORS for SPA
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Twilio Verify setup
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_VERIFY_SID = os.environ.get("TWILIO_VERIFY_SERVICE_SID", "")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Database placeholder (Supabase)
DATABASE_URL = os.environ.get("DATABASE_URL", "")
SUPABASE_API_KEY = os.environ.get("SUPABASE_API_KEY", "")

# TODO: initialize Supabase client here when available

# In-memory placeholder for user records
USERS = {}

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
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


def hash_phone(phone: str, salt: str) -> str:
    return hmac.new(salt.encode(), phone.encode(), hashlib.sha256).hexdigest()

@app.post("/auth/request-otp")
async def request_otp(data: OTPRequest):
    verification = twilio_client.verify.v2.services(TWILIO_VERIFY_SID).verifications.create(
        to=data.phone,
        channel="sms"
    )
    return {"status": verification.status}

@app.post("/auth/verify-otp")
async def verify_otp(data: OTPVerify):
    check = twilio_client.verify.v2.services(TWILIO_VERIFY_SID).verification_checks.create(
        to=data.phone,
        code=data.code
    )
    if check.status != "approved":
        raise HTTPException(status_code=400, detail="Invalid code")
    # store hashed phone with per-record salt
    salt = secrets.token_hex(8)
    hashed = hash_phone(data.phone, salt)
    USERS[hashed] = {"salt": salt}
    # TODO: save hashed phone and salt to database with user record
    return {"status": "verified", "id": hashed}

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
    return {"score": score}
