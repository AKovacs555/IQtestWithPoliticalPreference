import os
import time
from typing import Optional

import jwt
from fastapi import HTTPException, Header
from backend.db import get_user

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("JWT_SECRET", "change-me")
ALGORITHM = "HS256"


class User(dict):
    """Dict-like user object allowing attribute access."""

    def __getattr__(self, item):
        return self.get(item)


def create_token(user_id: str, is_admin: bool = False) -> str:
    """Generate a signed JWT containing the user's id and admin flag."""

    payload = {"user_id": user_id, "is_admin": is_admin, "iat": int(time.time())}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the current user from the Authorization header."""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User id missing")
    user_data = get_user(user_id)
    if not user_data:
        raise HTTPException(status_code=401, detail="User not found")
    return User(user_data)
