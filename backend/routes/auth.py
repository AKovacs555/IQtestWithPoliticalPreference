import random
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt

from backend.deps.auth import create_token
import backend.db as db


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterPayload(BaseModel):
    username: str | None = None
    email: str
    password: str
    referral_code: str | None = None


class LoginPayload(BaseModel):
    identifier: str
    password: str


@router.post("/register")
async def register(payload: RegisterPayload):
    """Create a new user using a username/email and password."""
    supabase = db.get_supabase()

    if payload.username:
        resp = (
            supabase.from_("users")
            .select("id")
            .eq("username", payload.username)
            .execute()
        )
        if resp.data:
            raise HTTPException(status_code=400, detail="Username already taken")

    resp = (
        supabase.from_("users").select("id").eq("email", payload.email).execute()
    )
    if resp.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    hashed_id = secrets.token_hex(16)

    referral_code = "".join(
        random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6)
    )

    data = {
        "hashed_id": hashed_id,
        "username": payload.username,
        "email": payload.email,
        "password_hash": password_hash,
        "free_tests": 0,
        "referrer_id": None,
        "referral_code": referral_code,
    }

    if payload.referral_code:
        try:
            ref_resp = (
                supabase.from_("users")
                .select("hashed_id")
                .eq("referral_code", payload.referral_code)
                .limit(1)
                .execute()
            )
            rows = ref_resp.data or []
            if rows:
                data["referrer_id"] = rows[0]["hashed_id"]
        except Exception:
            pass

    supabase.from_("users").insert(data).execute()
    token = create_token(hashed_id)
    return {"token": token, "user_id": hashed_id}


@router.post("/login")
async def login(payload: LoginPayload):
    """Authenticate a user using an email or username and password."""
    supabase = db.get_supabase()
    id_field = "email" if "@" in payload.identifier else "username"
    resp = (
        supabase.from_("users")
        .select("*")
        .eq(id_field, payload.identifier)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = rows[0]
    stored = user.get("password_hash") or ""
    if not bcrypt.checkpw(payload.password.encode(), stored.encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user["hashed_id"])
    return {"token": token, "user_id": user["hashed_id"]}

