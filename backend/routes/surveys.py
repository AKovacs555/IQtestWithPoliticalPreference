import random
import uuid
from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends

from backend.deps.auth import get_current_user
from backend import db

router = APIRouter(prefix="/surveys", tags=["surveys"])


@router.get("/daily3")
async def get_daily_three(lang: str = "ja", user: dict = Depends(get_current_user)):
    supabase = db.get_supabase()
    items_resp = (
        supabase.table("survey_items")
        .select("*")
        .eq("lang", lang)
        .eq("is_active", True)
        .execute()
    )
    items: List[dict] = items_resp.data or []

    today = date.today().isoformat()
    answered_resp = (
        supabase.table("survey_responses")
        .select("item_id")
        .eq("user_id", user["hashed_id"])
        .eq("answered_on", today)
        .execute()
    )
    answered_ids = {r["item_id"] for r in (answered_resp.data or [])}
    remaining = [i for i in items if i["id"] not in answered_ids]
    random.shuffle(remaining)
    return {"items": remaining[:3]}


@router.post("/answer")
async def answer_item(payload: dict, user: dict = Depends(get_current_user)):
    supabase = db.get_supabase()
    item_id = payload.get("item_id")
    answer_index = payload.get("answer_index")
    today = date.today().isoformat()
    now = datetime.utcnow().isoformat()
    table = supabase.table("survey_responses")
    existing = [
        r
        for r in supabase.tables.setdefault("survey_responses", [])
        if r.get("user_id") == user["hashed_id"]
        and r.get("item_id") == item_id
        and r.get("answered_on") == today
    ]
    if existing:
        table.update({"answer_index": answer_index, "created_at": now, "answered_on": today}).eq(
            "id", existing[0]["id"]
        ).execute()
    else:
        data = {
            "id": str(uuid.uuid4()),
            "user_id": user["hashed_id"],
            "item_id": item_id,
            "answer_index": answer_index,
            "created_at": now,
            "answered_on": today,
        }
        table.insert(data).execute()
    return {"status": "ok"}
