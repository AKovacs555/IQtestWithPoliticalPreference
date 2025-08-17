"""Public survey endpoints for the new poll schema."""
from __future__ import annotations

from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from backend.deps.auth import get_current_user
from backend import db

router = APIRouter(prefix="/surveys", tags=["surveys"])

class SubmitPayload(BaseModel):
    option_ids: List[str]
    other_texts: Dict[str, str] = Field(default_factory=dict)

@router.get("/available")
def available(lang: str, country: str, user: dict = Depends(get_current_user)):
    """Return surveys matching the user's language and country."""
    supabase = db.get_supabase()
    surveys = supabase.table("surveys").select("*").execute().data or []
    out = []
    for s in surveys:
        if s.get("lang") != lang:
            continue
        if s.get("status") != "approved":
            continue
        allowed = s.get("target_countries") or []
        if allowed and country not in allowed:
            continue
        genders = s.get("target_genders") or []
        user_gender = user.get("gender")
        if genders and user_gender not in genders:
            continue
        existing = (
            supabase.table("survey_answers")
            .select("id")
            .eq("survey_id", s["id"])
            .eq("user_id", user["hashed_id"])
            .execute()
            .data
            or []
        )
        if existing:
            continue
        items = (
            supabase.table("survey_items")
            .select("*")
            .eq("survey_id", s["id"])
            .eq("lang", s.get("lang"))
            .eq("is_active", True)
            .execute()
            .data
            or []
        )
        items = sorted(items, key=lambda o: o.get("position", 0))
        choices = []
        for o in items:
            txt = (
                o.get("body")
                or o.get("label")
                or o.get("text")
                or o.get("statement")
                or ""
            )
            choices.append(
                {
                    "option_id": o["id"],
                    "text": txt,
                    "label": txt,
                    "is_exclusive": o.get("is_exclusive", False),
                    "order": o.get("position"),
                }
            )
        out.append(
            {
                "survey_id": s["id"],
                "question_text": s.get("question_text") or s.get("question"),
                "selection": s.get("type"),
                "choices": choices,
            }
        )
    return out

@router.post("/{survey_id}/respond", status_code=201)
def respond(survey_id: str, payload: SubmitPayload, user: dict = Depends(get_current_user)):
    """Record responses for the given survey."""
    if not payload.option_ids:
        raise HTTPException(400, "option_ids required")
    supabase = db.get_supabase()
    # Persist into survey_answers for stats and record
    group_resp = supabase.table("surveys").select("group_id").eq("id", survey_id).execute()
    group_id = None
    if group_resp.data:
        group_id = group_resp.data[0].get("group_id")
    answer_rows = [
        {
            "survey_id": survey_id,
            "survey_group_id": group_id,
            "survey_item_id": oid,
            "user_id": user["hashed_id"],
        }
        for oid in payload.option_ids
    ]
    try:
        supabase.table("survey_answers").upsert(
            answer_rows, on_conflict="user_id,survey_item_id", ignore_duplicates=True
        ).execute()
    except TypeError:
        # In test environments, upsert might not support on_conflict kwargs
        supabase.table("survey_answers").upsert(answer_rows).execute()
    # Mark default survey as completed if applicable
    default_gid = db.get_dashboard_default_survey()
    if group_id and default_gid and str(group_id) == str(default_gid):
        try:
            # Update user's survey_completed flag
            db.update_user(db.get_supabase(), user["hashed_id"], {"survey_completed": True})
        except Exception as e:
            # Non-critical: log and continue
            import logging
            logging.getLogger(__name__).warning("Failed to update survey_completed for user %s: %s", user["id"], e)
    # Credit daily3 point if quota reached
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    if db.get_daily_answer_count(user["hashed_id"], today) >= 3:
        db.credit_points_once_per_day(str(user["id"]), 1, "daily_complete", {})
    return Response(status_code=201)

@router.get("/{survey_id}/stats")
def stats(survey_id: str):
    """Expose average IQ per option."""
    supabase = db.get_supabase()
    rows = (
        supabase.table("survey_option_iq_stats")
        .select("*")
        .eq("survey_id", survey_id)
        .execute()
        .data
        or []
    )
    return rows

# New endpoints for daily 3 polls
@router.get("/daily3")
def get_daily_three(lang: str, user: dict = Depends(get_current_user)):
    """Return up to 3 random polls for Daily 3 task (if not already completed)."""
    # Check if daily quota already completed
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    if db.get_daily_answer_count(user["hashed_id"], today) >= 3:
        # Already completed daily 3 polls
        raise HTTPException(status_code=409, detail={"error": "daily_quota_exceeded"})
    # Reuse available polls list and pick up to 3 randomly
    try:
        surveys_list = available(lang, user.get("nationality", ""), user)  # get list of eligible surveys
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load surveys")
    import random
    random.shuffle(surveys_list)
    return {"items": surveys_list[:3]}

@router.post("/answer")
def answer_poll(payload: Dict[str, int] = Depends(lambda: None), user: dict = Depends(get_current_user)):
    """Submit an answer for a single poll question (Daily 3 workflow)."""
    # The payload is expected to contain 'item_id' (survey_id) and 'answer_index'.
    if not payload or "item_id" not in payload or "answer_index" not in payload:
        raise HTTPException(status_code=400, detail="item_id and answer_index are required")
    survey_id = str(payload["item_id"])
    answer_idx = int(payload["answer_index"])
    supabase = db.get_supabase()
    # Ensure the user hasn't answered this question already
    existing = (
        supabase.table("survey_answers")
        .select("id")
        .eq("user_id", user["hashed_id"])
        .eq("survey_id", survey_id)
        .execute()
        .data
        or []
    )
    if existing:
        raise HTTPException(status_code=409, detail={"error": "already_answered"})
    # Fetch survey group and options
    resp = supabase.table("surveys").select("group_id, lang").eq("id", survey_id).single().execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Survey not found")
    group_id = resp.data.get("group_id")
    survey_lang = resp.data.get("lang")
    items_resp = supabase.table("survey_items").select("id").eq("survey_id", survey_id).eq("language", survey_lang).order("position").execute()
    options = items_resp.data or []
    if answer_idx < 0 or answer_idx >= len(options):
        raise HTTPException(status_code=400, detail="Invalid answer index")
    selected_item_id = options[answer_idx]["id"]
    answer_row = {
        "survey_id": survey_id,
        "survey_group_id": group_id,
        "survey_item_id": selected_item_id,
        "user_id": user["hashed_id"],
    }
    try:
        supabase.table("survey_answers").upsert(
            answer_row, on_conflict="user_id,survey_item_id", ignore_duplicates=True
        ).execute()
    except TypeError:
        supabase.table("survey_answers").upsert(answer_row).execute()
    # Credit daily point if quota reached
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()
    if db.get_daily_answer_count(user["hashed_id"], today) >= 3:
        db.credit_points_once_per_day(str(user["id"]), 1, "daily_complete", {})
    # Return empty success response
    return Response(status_code=201)
