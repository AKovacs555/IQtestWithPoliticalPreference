import os
import time
from typing import Optional

import jwt
from fastapi import HTTPException, Header

from backend.db import get_user

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
ALGORITHM = "HS256"


def create_token(user_id: str) -> str:
    payload = {"user_id": user_id, "iat": int(time.time())}
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    user = get_user(payload["user_id"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
