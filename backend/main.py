import os
import hashlib
import hmac
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from twilio.rest import Client

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

SALT = os.environ.get("PHONE_SALT", "static_salt")

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    code: str

def hash_phone(phone: str) -> str:
    return hmac.new(SALT.encode(), phone.encode(), hashlib.sha256).hexdigest()

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
    # store hashed phone
    hashed = hash_phone(data.phone)
    # TODO: save hashed phone to database with user record
    return {"status": "verified"}

@app.get("/ping")
async def ping():
    return {"message": "pong"}
