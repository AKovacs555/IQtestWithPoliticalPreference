import os
import time
from typing import Optional

import jwt
from fastapi import HTTPException, Header
from starlette.concurrency import run_in_threadpool
from backend.db import get_user, get_points
from backend.deps.supabase_jwt import decode_supabase_jwt

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


class User(dict):
    """Dict-like user object allowing attribute access."""

    def __getattr__(self, item):
        return self.get(item)


def create_token(user_id: str, is_admin: bool = False) -> str:
    """Generate a signed JWT containing the user's id and admin flag."""

    if not JWT_SECRET:
        raise RuntimeError(
            "SUPABASE_JWT_SECRET or JWT_SECRET environment variable must be set"
        )
    payload = {"user_id": user_id, "is_admin": is_admin, "iat": int(time.time())}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the current user from the Authorization header."""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    payload = decode_supabase_jwt(token)
    # Supabase JWTs store the user id in the ``sub`` claim. Older tokens issued
    # by our own backend used ``user_id`` instead, so check both for
    # compatibility.
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User id missing")
    user_data = await run_in_threadpool(get_user, user_id)
    if not user_data:
        raise HTTPException(status_code=401, detail="User not found")
    points = await run_in_threadpool(get_points, user_id)
    user_data["points"] = points
    return User(user_data)
