import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.deps.auth import get_current_user
from backend.db import get_daily_answer_count, insert_daily_answer

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
    return _quota(user["hashed_id"], datetime.utcnow())


@router.post("/answer")
async def answer(payload: DailyAnswer, user: dict = Depends(get_current_user)):
    insert_daily_answer(user["hashed_id"], payload.question_id, payload.answer)
    return _quota(user["hashed_id"], datetime.utcnow())
