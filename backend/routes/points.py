import os
from fastapi import APIRouter, Depends, HTTPException

from backend.deps.auth import get_current_user
from backend.db import (
    get_points,
    credit_points,
    credit_points_once_per_day,
)

AD_REWARD_POINTS = int(os.getenv("AD_REWARD_POINTS", "1"))
DAILY_REWARD_POINTS = int(os.getenv("DAILY_REWARD_POINTS", "1"))

router = APIRouter()


@router.get("/user/credits")
async def get_credits(user: dict = Depends(get_current_user)):
    """Return the current points balance for the authenticated user."""

    return {"points": get_points(str(user["id"]))}


@router.post("/points/ad_reward")
async def ad_reward(user: dict = Depends(get_current_user)):
    """Grant points for a verified ad reward."""

    credit_points(str(user["id"]), AD_REWARD_POINTS, "ad_reward", {})
    return {"points": get_points(str(user["id"]))}


@router.post("/points/daily_claim")
async def daily_claim(user: dict = Depends(get_current_user)):
    """Grant the daily completion reward if not already claimed today."""

    ok = credit_points_once_per_day(
        str(user["id"]), DAILY_REWARD_POINTS, "daily_complete", {}
    )
    if not ok:
        raise HTTPException(status_code=409, detail="already_claimed")
    return {"points": get_points(str(user["id"]))}

