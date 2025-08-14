"""Public survey endpoints for the new poll schema."""

from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

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
        if s.get("language") != lang:
            continue
        if s.get("status") != "approved":
            continue
        allowed = s.get("allowed_countries") or []
        if allowed and country not in allowed:
            continue
        # Exclude already answered surveys for this user
        existing = (
            supabase.table("survey_responses")
            .select("survey_id")
            .eq("survey_id", s["id"])
            .eq("user_id", user["hashed_id"])
            .execute()
            .data
            or []
        )
        if existing:
            continue
        opts = (
            supabase.table("survey_options")
            .select("*")
            .eq("survey_id", s["id"])
            .execute()
            .data
            or []
        )
        opts = sorted(opts, key=lambda o: o.get("order", 0))
        out.append(
            {
                "survey_id": s["id"],
                "survey_group_id": s.get("survey_group_id"),
                "question_text": s.get("question_text"),
                "selection_type": s.get("selection_type"),
                "options": [
                    {
                        "option_id": o["id"],
                        "text": o["option_text"],
                        "is_exclusive": o.get("is_exclusive", False),
                        "requires_text": o.get("requires_text", False),
                        "order": o.get("order"),
                    }
                    for o in opts
                ],
            }
        )
    return out


@router.post("/{survey_id}/respond", status_code=201)
def respond(
    survey_id: str, payload: SubmitPayload, user: dict = Depends(get_current_user)
):
    """Record responses for the given survey."""

    if not payload.option_ids:
        raise HTTPException(400, "option_ids required")
    supabase = db.get_supabase()
    response_group_id = str(uuid4())
    rows = [
        {
            "response_group_id": response_group_id,
            "survey_id": survey_id,
            "user_id": user["hashed_id"],
            "option_id": oid,
            "other_text": payload.other_texts.get(oid),
        }
        for oid in payload.option_ids
    ]
    supabase.table("survey_responses").insert(rows).execute()
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

