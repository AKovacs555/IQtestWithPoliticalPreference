"""Public survey endpoints for the new poll schema."""

from __future__ import annotations

from typing import Dict, List
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from backend.deps.auth import get_current_user
from backend.deps.supabase_client import get_supabase_client
from backend.utils.settings import get_setting_int
from backend import db


router = APIRouter(prefix="/surveys", tags=["surveys"])


class SubmitPayload(BaseModel):
    option_ids: List[str]
    other_texts: Dict[str, str] = Field(default_factory=dict)


class AnswerPayload(BaseModel):
    item_id: str
    answer_index: int


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


@router.post("/answer")
def daily_answer(payload: AnswerPayload, user: dict = Depends(get_current_user)):
    """Record a daily survey answer and grant points after three responses."""

    db.insert_daily_answer(user["hashed_id"], payload.item_id)
    answered_count = db.get_daily_answer_count(user["hashed_id"], datetime.utcnow().date())
    if answered_count >= 3:
        supabase = get_supabase_client()
        reward = get_setting_int(supabase, "daily_reward_points", 1)
        db.insert_point_ledger(user["hashed_id"], reward, reason="daily3")
        db.update_user(supabase, user["hashed_id"], {"survey_completed": True})
    return {"answered": answered_count, "required": 3}


@router.post("/{survey_id}/respond", status_code=201)
def respond(
    survey_id: str, payload: SubmitPayload, user: dict = Depends(get_current_user)
):
    """Record responses for the given survey."""

    if not payload.option_ids:
        raise HTTPException(400, "option_ids required")
    supabase = db.get_supabase()

    # Persist into survey_answers for arena stats
    group_resp = (
        supabase.table("surveys")
        .select("group_id")
        .eq("id", survey_id)
        .execute()
    )
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
            answer_rows,
            on_conflict="user_id,survey_item_id",
            ignore_duplicates=True,
        ).execute()
    except TypeError:
        # Test double lacks upsert kwargs support
        supabase.table("survey_answers").upsert(answer_rows).execute()
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

