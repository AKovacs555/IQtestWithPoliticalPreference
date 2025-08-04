import os
import random
import time
import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt

from backend.sms_service import send_otp
from backend.deps.auth import create_token
from backend.deps.supabase_client import get_supabase_client

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory store for verification codes
_codes: dict[str, tuple[str, float]] = {}
CODE_TTL = 300  # seconds


class SendCodePayload(BaseModel):
    phone: str


class VerifyCodePayload(BaseModel):
    phone: str
    code: str


class RegisterPayload(BaseModel):
    phone: str
    email: str
    password: str
    code: str
    referral_code: str | None = None


class LoginPayload(BaseModel):
    identifier: str
    password: str


def normalize_phone(phone: str) -> str:
    # Remove spaces and dashes
    p = phone.strip().replace(" ", "").replace("-", "")
    # If no '+' prefix, assume it's a Japanese number and prepend +81
    if not p.startswith("+"):
        p = "+81" + p.lstrip("0")
    return p


def _save_code(phone: str, code: str) -> None:
    _codes[phone] = (code, time.time() + CODE_TTL)


def _check_code(phone: str, code: str) -> bool:
    entry = _codes.get(phone)
    if not entry:
        return False
    value, expiry = entry
    if time.time() > expiry:
        _codes.pop(phone, None)
        return False
    return value == code


@router.post("/send-code")
async def send_code(payload: SendCodePayload):
    code = f"{random.randint(0, 999999):06d}"
    phone = normalize_phone(payload.phone)
    _save_code(phone, code)
    try:
        send_otp(phone, code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "sent"}


@router.post("/verify-code")
async def verify_code(payload: VerifyCodePayload):
    phone = normalize_phone(payload.phone)
    if _check_code(phone, payload.code):
        return {"status": "verified"}
    raise HTTPException(status_code=400, detail="Invalid code")


@router.post("/register")
async def register(payload: RegisterPayload):
    phone = normalize_phone(payload.phone)
    if not _check_code(phone, payload.code):
        raise HTTPException(status_code=400, detail="Invalid code")
    supabase = get_supabase_client()
    password_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    hashed_id = secrets.token_hex(16)
    referral_code = ''.join(random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
    data = {
        "hashed_id": hashed_id,
        "phone": phone,
        "email": payload.email,
        "password_hash": password_hash,
        "free_tests": 0,
        "referrer_id": None,
        "referral_code": referral_code,
    }
    if payload.referral_code:
        try:
            resp = (
                supabase.table("users")
                .select("hashed_id")
                .eq("referral_code", payload.referral_code)
                .limit(1)
                .execute()
            )
            rows = resp.data or []
            if rows:
                data["referrer_id"] = rows[0]["hashed_id"]
        except Exception:
            pass
    supabase.table("users").insert(data).execute()
    token = create_token(hashed_id)
    return {"token": token, "user_id": hashed_id}


@router.post("/login")
async def login(payload: LoginPayload):
    supabase = get_supabase_client()
    resp = (
        supabase.table("users")
        .select("*")
        .or_(f"phone.eq.{payload.identifier},email.eq.{payload.identifier}")
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=400, detail="User not found")
    user = rows[0]
    stored = user.get("password_hash") or ""
    if not bcrypt.checkpw(payload.password.encode(), stored.encode()):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_token(user["hashed_id"])
    return {"token": token, "user_id": user["hashed_id"]}
