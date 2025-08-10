from fastapi import APIRouter, Depends, HTTPException
from db import get_supabase, update_user
from .dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin-users"])


@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users():
    """Return a list of all users with their hashed_id and free_attempts."""
    supabase = get_supabase()
    rows = supabase.from_("app_users").select("hashed_id, free_attempts").execute().data
    return {"users": rows or []}


@router.post("/user/free_attempts", dependencies=[Depends(require_admin)])
async def update_free_attempts(payload: dict):
    """
    Update the free_attempts value for a given user.
    Expects JSON body: { "user_id": "<hashed_id>", "free_attempts": <int> }.
    """
    user_id = payload.get("user_id")
    free_attempts = payload.get("free_attempts")
    if user_id is None or free_attempts is None:
        raise HTTPException(status_code=400, detail="Missing parameters")
    supabase = get_supabase()
    update_user(supabase, user_id, {"free_attempts": free_attempts})
    return {"status": "ok"}
