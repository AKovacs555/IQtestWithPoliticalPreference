from fastapi import APIRouter, Depends, HTTPException
from backend.deps.auth import get_current_user  # verifies JWT
from backend.core.supabase_admin import supabase_admin  # service role client

router = APIRouter()

@router.post("/user/ensure")
def ensure_profile(user=Depends(get_current_user)):
    uid = str(user["id"] if isinstance(user, dict) else getattr(user, "id"))
    email = None
    if isinstance(user, dict):
        email = user.get("email")
    else:
        email = getattr(user, "email", None)

    payload = {"id": uid, "hashed_id": uid}
    if email:
        payload["email"] = email

    try:
        res = supabase_admin.table("app_users").upsert(payload).execute()
        if hasattr(res, "error") and res.error:
            raise HTTPException(status_code=500, detail=str(res.error))
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
