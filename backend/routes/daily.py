import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..deps.auth import get_current_user
from ..db import (
    get_daily_answer_count,
    insert_daily_answer,
    update_user,
    daily_reward_claim,
    get_points,
)
from ..deps.supabase_client import get_supabase_client

router = APIRouter(prefix="/daily", tags=["daily"])
logger = logging.getLogger(__name__)


class DailyAnswer(BaseModel):
    question_id: str
    answer: dict | None = None


def _quota(user_id: str, now: datetime) -> dict:
    today = now.date()
    count = get_daily_answer_count(user_id, today)
    reset_at = (
        datetime.combine(today, datetime.min.time()) + timedelta(days=1)
    ).isoformat() + "Z"
    if count == 0:
        logger.info("daily3_reset_detected")
    return {"answered": count, "required": 3, "reset_at": reset_at}


@router.get("/quota")
async def quota(user: dict = Depends(get_current_user)):
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    return _quota(user["hashed_id"], now)


@router.post("/answer")
async def answer(payload: DailyAnswer, user: dict = Depends(get_current_user)):
    insert_daily_answer(user["hashed_id"], payload.question_id, payload.answer)
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    answered_count = get_daily_answer_count(user["hashed_id"], now.date())
    if answered_count >= 3:
        granted = daily_reward_claim(str(user["id"]))
        if granted:
            supabase = get_supabase_client()
            update_user(supabase, user["hashed_id"], {"survey_completed": True})
    return _quota(user["hashed_id"], now)


@router.post("/claim")
async def claim(user: dict = Depends(get_current_user)):
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    if get_daily_answer_count(user["hashed_id"], now.date()) < 3:
        return {"granted": False, "points": get_points(str(user["id"]))}
    granted = daily_reward_claim(str(user["id"]))
    return {"granted": granted, "points": get_points(str(user["id"]))}
