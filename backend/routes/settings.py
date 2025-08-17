from fastapi import APIRouter, Depends, HTTPException
from backend.routes.dependencies import get_current_user, is_admin
from backend.utils.settings import supabase, get_setting

router = APIRouter()

@router.get("/settings/{key}")
async def read_setting(key: str, user=Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admins only")
    value = await get_setting(key)
    return {"key": key, "value": value}

@router.post("/settings/update")
async def update_setting(key: str, value: int, user = Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admins only")
    supabase.table("settings").upsert({"key": key, "value": value}).execute()
    return {"status": "ok"}
