import os
from fastapi import APIRouter, Header, HTTPException, Depends
from db import get_supabase

router = APIRouter(prefix="/admin", tags=["admin-users"])

def check_admin(x_admin_api_key: str | None = Header(None, alias="X-Admin-Api-Key")):
    if x_admin_api_key != os.getenv("ADMIN_API_KEY"):
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/users", dependencies=[Depends(check_admin)])
async def list_users():
    supabase = get_supabase()
    rows = supabase.from_("users").select("hashed_id, free_attempts").execute().data
    return {"users": rows or []}

@router.post("/user/free_attempts", dependencies=[Depends(check_admin)])
async def update_free_attempts(payload: dict):
    user_id = payload.get("user_id")
    free_attempts = payload.get("free_attempts")
    if user_id is None or free_attempts is None:
        raise HTTPException(status_code=400, detail="Missing parameters")
    supabase = get_supabase()
    supabase.from_("users").update({"free_attempts": free_attempts}).eq("hashed_id", user_id).execute()
    return {"status": "ok"}
