import os
from fastapi import APIRouter, Depends, Header, HTTPException
from db import get_supabase

router = APIRouter(prefix="/admin", tags=["admin-users"])


def check_admin(x_admin_api_key: str | None = Header(None, alias="X-Admin-Api-Key")):
    """Validate the provided admin API key."""
    expected = os.getenv("ADMIN_API_KEY")
    if x_admin_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/users", dependencies=[Depends(check_admin)])
async def list_users():
    """Return a list of all users with their hashed_id and free_attempts."""
    supabase = get_supabase()
    rows = supabase.from_("users").select("hashed_id, free_attempts").execute().data
    return {"users": rows or []}


@router.post("/user/free_attempts", dependencies=[Depends(check_admin)])
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
    supabase.from_("users").update({"free_attempts": free_attempts}).eq("hashed_id", user_id).execute()
    return {"status": "ok"}
