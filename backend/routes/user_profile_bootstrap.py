from fastapi import APIRouter, Header, HTTPException
from backend.deps.supabase_jwt import decode_supabase_jwt
from backend.core.supabase_admin import supabase_admin  # service role client

router = APIRouter()

@router.post("/user/ensure")
def ensure_profile(authorization: str = Header(None)):
    """Create a user profile if it doesn't exist yet.

    This endpoint bypasses the standard database lookup required by
    ``get_current_user`` and instead trusts any valid Supabase JWT. The token
    is decoded to extract the user id (from ``sub`` or ``user_id``) and, if
    present, the user's email. The resulting data is upserted into the
    ``app_users`` table using the service-role Supabase client.
    """

    # Validate Authorization header and extract token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing header")
    token = authorization.split(" ", 1)[1]

    try:
        payload = decode_supabase_jwt(token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="no sub")

    data = {"id": str(user_id), "hashed_id": str(user_id)}
    email = payload.get("email")
    if email:
        data["email"] = email

    res = supabase_admin.table("app_users").upsert(data).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=str(res.error))

    # Fetch is_admin flag for the user
    res = (
        supabase_admin.table("app_users")
        .select("is_admin")
        .eq("id", str(user_id))
        .single()
        .execute()
    )
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=str(res.error))
    is_admin = bool(res.data.get("is_admin")) if res.data else False

    # Propagate is_admin to auth metadata
    try:
        supabase_admin.auth.admin.update_user_by_id(
            str(user_id), {"app_metadata": {"is_admin": is_admin}}
        )
    except Exception as e:  # pragma: no cover - supabase client handles errors
        if "no changes" not in str(e).lower():
            raise HTTPException(status_code=500, detail=str(e))

    return {"ok": True, "is_admin": is_admin}
