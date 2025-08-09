from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends

from backend.deps.auth import get_current_user
from backend import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daily", tags=["daily"])


# Internal helper to allow monkeypatching in tests

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _day_start(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)


@router.get("/quota")
async def get_quota(user: dict = Depends(get_current_user)) -> dict[str, Any]:
    now = _utc_now()
    start = _day_start(now)
    reset_at = start + timedelta(days=1)
    answered = db.get_daily_answer_count(user["hashed_id"], start)
    if answered == 0:
        yesterday = start - timedelta(days=1)
        if db.get_daily_answer_count(user["hashed_id"], yesterday) > 0:
            logger.info("daily3_reset_detected")
    return {"answered": answered, "required": 3, "reset_at": reset_at.isoformat()}


@router.post("/answer")
async def answer_item(payload: dict, user: dict = Depends(get_current_user)) -> dict[str, Any]:
    now = _utc_now()
    start = _day_start(now)
    db.insert_daily_answer(
        user["hashed_id"],
        str(payload.get("item_id")),
        int(payload.get("answer_index", 0)),
        now,
    )
    answered = db.get_daily_answer_count(user["hashed_id"], start)
    reset_at = start + timedelta(days=1)
    return {"answered": answered, "required": 3, "reset_at": reset_at.isoformat()}
