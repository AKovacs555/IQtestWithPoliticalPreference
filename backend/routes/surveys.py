import random
import uuid
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.deps.auth import get_current_user
from backend import db

router = APIRouter(prefix="/surveys", tags=["surveys"])


@router.get("/daily3")
async def get_daily_three(lang: str = "ja", user: dict = Depends(get_current_user)):
    supabase = db.get_supabase()
    today = date.today().isoformat()
    answered_today = db.count_daily_survey_responses(user["hashed_id"], today)
    if answered_today >= 3:
        raise HTTPException(status_code=409, detail={"error": "daily_quota_exceeded"})

    items_resp = (
        supabase.table("survey_items")
        .select("*")
        .eq("lang", lang)
        .eq("is_active", True)
        .execute()
    )
    items: List[dict] = items_resp.data or []

    answered_resp = (
        supabase.table("survey_responses")
        .select("item_id")
        .eq("user_id", user["hashed_id"])
        .execute()
    )
    answered_ids = {r["item_id"] for r in (answered_resp.data or [])}
    remaining = [i for i in items if i["id"] not in answered_ids]
    random.shuffle(remaining)
    return {"items": remaining[: max(0, 3 - answered_today)]}


@router.post("/answer")
async def answer_item(payload: dict, user: dict = Depends(get_current_user)):
    supabase = db.get_supabase()
    item_id = payload.get("item_id")
    answer_index = payload.get("answer_index")
    today = date.today().isoformat()
    now = datetime.utcnow().isoformat()

    answered_today = db.count_daily_survey_responses(user["hashed_id"], today)
    if answered_today >= 3:
        raise HTTPException(status_code=409, detail={"error": "daily_quota_exceeded"})

    existing = db.get_daily_survey_response(user["hashed_id"], item_id, today)
    if existing:
        raise HTTPException(status_code=409, detail={"error": "already_answered"})

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user["hashed_id"],
        "item_id": item_id,
        "answer_index": answer_index,
        "created_at": now,
        "answered_on": today,
    }
    supabase.table("survey_responses").insert(data).execute()
    return {"status": "ok"}
