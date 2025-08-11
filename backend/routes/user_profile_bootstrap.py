from fastapi import APIRouter, Depends, HTTPException
from backend.deps.auth import get_current_user  # verifies JWT
from backend.core.supabase import supabase_admin  # service role client

router = APIRouter()

@router.post("/user/ensure")
def ensure_profile(user=Depends(get_current_user)):
    uid = str(user["id"] if isinstance(user, dict) else user.id)
    email = user.get("email") if isinstance(user, dict) else getattr(user, "email", None)
    data = {"id": uid, "hashed_id": uid}
    if email:
        data["email"] = email
    res = supabase_admin.table("app_users").upsert(data).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=str(res.error))
    return {"ok": True}
