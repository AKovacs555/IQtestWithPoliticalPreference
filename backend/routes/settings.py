from fastapi import APIRouter, Depends, HTTPException
from .dependencies import get_current_user, is_admin
from backend.deps.supabase_client import get_supabase_client
from backend.utils.settings import get_setting_int

router = APIRouter()

@router.get("/settings/{key}")
async def read_setting(key: str, user=Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admins only")
    client = get_supabase_client()
    value = get_setting_int(client, key, 0)
    return {"key": key, "value": value}

@router.post("/settings/update")
async def update_setting(key: str, value: int, user = Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="Admins only")
    client = get_supabase_client()
    client.table("settings").upsert({"key": key, "value": value}).execute()
    return {"status": "ok"}
