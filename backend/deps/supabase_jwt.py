import os
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_JWKS_URL = os.getenv("SUPABASE_JWKS_URL") or (
    f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json" if SUPABASE_URL else None
)
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("JWT_SECRET")
VERIFY_OPTS = {"verify_aud": False}


def decode_supabase_jwt(token: str) -> dict:
    """Decode Supabase JWT supporting HS and JWKS-based verification."""
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token header")

    alg = header.get("alg", "HS256")

    if JWT_SECRET and alg.startswith("HS"):
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[alg], options=VERIFY_OPTS)
        except Exception:
            pass

    if not SUPABASE_JWKS_URL:
        raise HTTPException(status_code=401, detail="JWT verification not configured")

    try:
        jwk_client = PyJWKClient(SUPABASE_JWKS_URL)
        signing_key = jwk_client.get_signing_key_from_jwt(token)
        return jwt.decode(token, signing_key.key, algorithms=[alg], options=VERIFY_OPTS)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

