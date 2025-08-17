from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.deps.auth import get_current_user
from backend.deps.supabase_client import get_supabase_client

router = APIRouter(prefix="/ads", tags=["ads"])

class AdStartPayload(BaseModel):
    pass

@router.post("/start")
async def ads_start(user: dict = Depends(get_current_user)):
    return {"status": "started"}

@router.post("/complete")
async def ads_complete(user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    supabase.rpc("award_points", {"p_user_id": str(user["id"]), "p_delta": 1}).execute()
    new_points = (
        supabase.table("app_users")
        .select("points")
        .eq("id", user["id"])
        .single()
        .execute()
        .data["points"]
    )
    return {"points": new_points}
