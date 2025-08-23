"""Endpoint to fetch the next unanswered survey question."""

from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from backend import db
from backend.deps.auth import get_current_user


router = APIRouter(prefix="/survey", tags=["survey"])


@router.get("/start")
def start(lang: str = "en", user: Dict = Depends(get_current_user)):
    """Return an unanswered survey for the user with language fallback."""

    supabase = db.get_supabase()

    # 1. Fetch user row and previously answered survey group ids
    user_id = user.get("id")
    ures = (
        supabase.table("app_users").select("*").eq("id", user_id).single().execute()
    )
    user_row = ures.data or {}
    answered = (
        supabase.table("survey_answers")
        .select("survey_group_id")
        .eq("user_id", user_id)
        .execute()
        .data
        or []
    )
    answered_group_ids = {r["survey_group_id"] for r in answered if r.get("survey_group_id")}

    # 2. Candidate languages with English fallback
    langs = [lang, "en"] if lang != "en" else ["en"]

    # 3. Filtering conditions
    nationality = user_row.get("nationality")
    gender = (user_row.get("demographic") or {}).get("gender")

    def pick_one(lang_code: str):
        q = (
            supabase.table("surveys")
            .select("*")
            .eq("status", "approved")
            .eq("is_active", True)
            .eq("lang", lang_code)
            .order("created_at", desc=True)
            .execute()
        )
        rows = q.data or []
        filtered: List[dict] = []
        for r in rows:
            if r.get("group_id") in answered_group_ids:
                continue
            countries = r.get("target_countries") or []
            if countries and nationality not in countries:
                continue
            genders = r.get("target_genders") or []
            if genders and gender not in genders:
                continue
            filtered.append(r)
        return filtered[0] if filtered else None

    survey = None
    for lc in langs:
        survey = pick_one(lc)
        if survey:
            break
    if not survey:
        raise HTTPException(404, detail={"error": "no_survey_available"})

    # 4. Fetch survey items with fallback to English
    items = (
        supabase.table("survey_items")
        .select("id,body,is_exclusive,position,lang")
        .eq("survey_id", survey["id"])
        .eq("lang", survey["lang"])
        .order("position")
        .execute()
        .data
        or []
    )
    if not items and survey["lang"] != "en":
        items = (
            supabase.table("survey_items")
            .select("id,body,is_exclusive,position,lang")
            .eq("survey_id", survey["id"])
            .eq("lang", "en")
            .order("position")
            .execute()
            .data
            or []
        )

    return {"survey": survey, "items": items}

