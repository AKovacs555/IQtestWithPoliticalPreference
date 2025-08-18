from fastapi import APIRouter, Depends, HTTPException
from .dependencies import require_admin
from backend.utils.settings import supabase, get_setting

router = APIRouter(prefix="/admin/points", tags=["admin-points"])

CONFIG_KEYS = [
    "signup_reward_points",
    "invite_reward_points",
    "daily_reward_points",
    "ad_reward_points",
    "attempt_cost_points",
]


@router.get("/config", dependencies=[Depends(require_admin)])
async def get_config():
    values = {}
    for key in CONFIG_KEYS:
        val = await get_setting(key, 0)
        try:
            values[key] = int(val)
        except (TypeError, ValueError):
            values[key] = 0
    return values


@router.put("/config", dependencies=[Depends(require_admin)])
async def update_config(payload: dict):
    for key in CONFIG_KEYS:
        if key in payload:
            val = payload[key]
            if not isinstance(val, int) or val < 0:
                raise HTTPException(status_code=400, detail=f"Invalid value for {key}")
            supabase.table("settings").upsert({"key": key, "value": val}).execute()
    return {"status": "ok"}

