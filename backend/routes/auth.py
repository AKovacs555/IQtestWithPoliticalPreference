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
    inviter_code: str | None = None


class LoginPayload(BaseModel):
    identifier: str
    password: str


@router.post("/register")
async def register(payload: RegisterPayload):
    """Create a new user using a username/email and password."""
    supabase = db.get_supabase()

    if payload.username:
        resp = (
            supabase.from_("app_users")
            .select("hashed_id")
            .eq("username", payload.username)
            .execute()
        )
        if resp.data:
            raise HTTPException(status_code=400, detail="Username already taken")

    resp = (
        supabase.from_("app_users").select("hashed_id").eq("email", payload.email).execute()
    )
    if resp.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = bcrypt.hashpw(payload.password.encode(), bcrypt.gensalt()).decode()
    hashed_id = secrets.token_hex(16)

    data = {
        "hashed_id": hashed_id,
        "username": payload.username,
        "email": payload.email,
        "password_hash": password_hash,
    }

    inviter = None
    if payload.inviter_code:
        inviter = (
            supabase.from_("app_users")
            .select("hashed_id")
            .eq("invite_code", payload.inviter_code)
            .single()
            .execute()
            .data
        )
        if inviter and inviter.get("hashed_id") != hashed_id:
            data["referred_by"] = inviter.get("hashed_id")
        else:
            inviter = None

    db.create_user(data)
    if inviter:
        supabase.table("referrals").insert(
            {
                "inviter_code": payload.inviter_code,
                "invitee_user": hashed_id,
                "credited": False,
            }
        ).execute()
    token = create_token(hashed_id, False)
    return {"token": token, "user_id": hashed_id, "is_admin": False}


@router.post("/login")
async def login(payload: LoginPayload):
    """Authenticate a user using an email or username and password."""
    supabase = db.get_supabase()
    id_field = "email" if "@" in payload.identifier else "username"
    resp = (
        supabase.from_("app_users")
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
    token = create_token(user["hashed_id"], bool(user.get("is_admin")))
    return {"token": token, "user_id": user["hashed_id"], "is_admin": bool(user.get("is_admin"))}

