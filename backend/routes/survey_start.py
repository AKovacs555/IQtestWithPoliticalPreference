"""Endpoint to fetch the next unanswered survey question."""

from __future__ import annotations

import random
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from backend import db
from backend.deps.auth import get_current_user


router = APIRouter(prefix="/survey", tags=["survey"])


@router.get("/start")
def start(lang: str = "en", user: Dict = Depends(get_current_user)):
    """Return a single unanswered survey for the user.

    Surveys are filtered by language, target country/gender and previous
    answers. If no survey in the requested language is available, a fallback
    English version from the same group is returned.
    """

    supabase = db.get_supabase()

    nationality = user.get("nationality")
    gender = (user.get("demographic") or {}).get("gender") or "other"

    # Fetch answered group ids to avoid duplicates
    answered = set(db.get_answered_survey_group_ids(user["hashed_id"]))

    # Fetch candidate surveys in requested language or English for fallback
    resp = (
        supabase.table("surveys")
        .select("*")
        .in_("lang", [lang, "en"])
        .eq("status", "approved")
        .eq("is_active", True)
        .execute()
    )
    surveys = resp.data or []

    # Choose best language per group
    grouped: Dict[str, dict] = {}
    for s in surveys:
        gid = str(s.get("group_id"))
        current = grouped.get(gid)
        if current is None or (current.get("lang") != lang and s.get("lang") == lang):
            grouped[gid] = s

    candidates: List[dict] = []
    for s in grouped.values():
        if str(s.get("group_id")) in answered:
            continue
        countries = s.get("target_countries") or []
        if countries and nationality not in countries:
            continue
        genders = s.get("target_genders") or []
        if genders and gender not in genders:
            continue
        candidates.append(s)

    if not candidates:
        raise HTTPException(404, "no_survey_available")

    survey = random.choice(candidates)

    items = (
        supabase.table("survey_items")
        .select("*")
        .eq("survey_id", survey["id"])
        .eq("language", survey.get("lang"))
        .eq("is_active", True)
        .execute()
        .data
        or []
    )
    items = sorted(items, key=lambda o: o.get("position", 0))
    choices = [
        {
            "label": i.get("body", ""),
            "exclusive": i.get("is_exclusive", False),
            "position": i.get("position"),
        }
        for i in items
    ]

    return {
        "survey_id": survey["id"],
        "group_id": survey.get("group_id"),
        "title": survey.get("title"),
        "question": survey.get("question_text"),
        "type": survey.get("type"),
        "is_single_choice": survey.get("is_single_choice"),
        "choices": choices,
    }

