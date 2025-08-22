import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.deps.auth import get_current_user
from backend.db import (
    get_daily_answer_count,
    insert_daily_answer,
    insert_point_ledger,
    update_user,
)
from backend.utils.settings import get_setting_int
from backend.deps.supabase_client import get_supabase_client

router = APIRouter(prefix="/daily", tags=["daily"])
logger = logging.getLogger(__name__)


class DailyAnswer(BaseModel):
    question_id: str


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
    return _quota(user["hashed_id"], datetime.utcnow())


@router.post("/answer")
async def answer(payload: DailyAnswer, user: dict = Depends(get_current_user)):
    insert_daily_answer(user["hashed_id"], payload.question_id)
    answered_count = get_daily_answer_count(user["hashed_id"], datetime.utcnow().date())
    if answered_count >= 3:
        supabase = get_supabase_client()
        reward = get_setting_int(supabase, "daily_reward_points", 1)
        insert_point_ledger(user["hashed_id"], reward, reason="daily3")
        update_user(supabase, user["hashed_id"], {"survey_completed": True})
    return _quota(user["hashed_id"], datetime.utcnow())
