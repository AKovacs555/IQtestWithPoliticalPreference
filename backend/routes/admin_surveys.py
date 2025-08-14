"""Admin endpoints for managing surveys using the new schema."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from backend.routes.dependencies import require_admin
from backend import db


router = APIRouter(
    prefix="/admin/surveys",
    tags=["admin-surveys"],
    dependencies=[Depends(require_admin)],
)


def grant_free_attempts(countries: list[str]) -> None:  # pragma: no cover - legacy hook
    """Legacy helper retained for backward compatibility.

    Older parts of the codebase import this function from ``admin_surveys`` to
    reward users in specific countries. The new survey implementation no longer
    uses it but keeping a no-op stub avoids import errors until callers migrate.
    """
    if not countries:
        return
    supabase = db.get_supabase()
    supabase.table("app_users").select("hashed_id").execute()


def _now_iso() -> str:
    """Return current UTC time as ISO formatted string."""

    return datetime.utcnow().isoformat() + "Z"


class OptionIn(BaseModel):
    """Incoming survey option definition."""

    text: str
    is_exclusive: bool = False
    requires_text: bool = False
    order: int


class SurveyCreate(BaseModel):
    """Payload for creating or replacing a survey."""

    title: str
    question_text: str
    language: str
    allowed_countries: List[str] = Field(default_factory=list)
    selection_type: Literal["single", "multiple"] = "single"
    status: Literal["pending", "approved"] = "pending"
    options: List[OptionIn]
    auto_translate: bool = False  # Placeholder; translation handled elsewhere


@router.post("/")
def create_survey(payload: SurveyCreate):
    """Insert a new survey and its options.

    The function intentionally keeps the implementation simple: translation and
    cross-language cloning are omitted for now. Each option is assigned a fresh
    ``option_group_id`` so future translations can reference it."""

    supabase = db.get_supabase()
    survey_group_id = str(uuid4())
    approved_at = _now_iso() if payload.status == "approved" else None
    survey_row = {
        "survey_group_id": survey_group_id,
        "title": payload.title,
        "question_text": payload.question_text,
        "language": payload.language,
        "allowed_countries": payload.allowed_countries,
        "selection_type": payload.selection_type,
        "status": payload.status,
        "approved_at": approved_at,
    }
    res = (
        supabase.table("surveys")
        .insert(survey_row, returning="representation")
        .execute()
    )
    if not res.data:
        raise HTTPException(500, "failed to insert survey")
    survey_id = res.data[0]["id"]

    option_rows = [
        {
            "survey_id": survey_id,
            "option_text": opt.text,
            "order": opt.order,
            "is_exclusive": opt.is_exclusive,
            "requires_text": opt.requires_text,
            "option_group_id": str(uuid4()),
        }
        for opt in payload.options
    ]
    if option_rows:
        supabase.table("survey_options").insert(
            option_rows, returning="representation"
        ).execute()

    created = res.data[0]
    created["options"] = option_rows
    return created


class SurveyUpdate(SurveyCreate):
    """Identical to :class:`SurveyCreate` for now."""


@router.put("/{survey_id}")
def update_survey(survey_id: str, payload: SurveyUpdate):
    """Replace a survey and its options."""

    supabase = db.get_supabase()
    approved_at = _now_iso() if payload.status == "approved" else None
    data = {
        "title": payload.title,
        "question_text": payload.question_text,
        "language": payload.language,
        "allowed_countries": payload.allowed_countries,
        "selection_type": payload.selection_type,
        "status": payload.status,
        "approved_at": approved_at,
    }
    supabase.table("surveys").update(data).eq("id", survey_id).execute()
    # Full replacement of options
    supabase.table("survey_options").delete().eq("survey_id", survey_id).execute()
    option_rows = [
        {
            "survey_id": survey_id,
            "option_text": opt.text,
            "order": opt.order,
            "is_exclusive": opt.is_exclusive,
            "requires_text": opt.requires_text,
            "option_group_id": str(uuid4()),
        }
        for opt in payload.options
    ]
    if option_rows:
        supabase.table("survey_options").insert(option_rows).execute()
    return {"id": survey_id}


@router.delete("/{survey_id}", status_code=204)
def delete_survey(survey_id: str):
    """Delete all variants of the survey identified by ``survey_id``."""

    supabase = db.get_supabase()
    res = (
        supabase.table("surveys")
        .select("survey_group_id")
        .eq("id", survey_id)
        .execute()
    )
    data = res.data or []
    if not data:
        return Response(status_code=204)
    group_id = data[0]["survey_group_id"]
    supabase.table("surveys").delete().eq("survey_group_id", group_id).execute()
    return Response(status_code=204)


def _set_status(survey_id: str, status: Literal["approved", "rejected"]):
    supabase = db.get_supabase()
    res = (
        supabase.table("surveys")
        .select("survey_group_id")
        .eq("id", survey_id)
        .execute()
    )
    data = res.data or []
    if not data:
        raise HTTPException(404, "survey not found")
    group_id = data[0]["survey_group_id"]
    update = {"status": status}
    if status == "approved":
        update["approved_at"] = _now_iso()
    supabase.table("surveys").update(update).eq(
        "survey_group_id", group_id
    ).execute()


@router.post("/{survey_id}/approve")
def approve_survey(survey_id: str):
    """Mark all surveys in the group as approved."""

    _set_status(survey_id, "approved")
    return {"status": "approved"}


@router.post("/{survey_id}/reject")
def reject_survey(survey_id: str):
    """Mark all surveys in the group as rejected."""

    _set_status(survey_id, "rejected")
    return {"status": "rejected"}


@router.get("/")
def list_surveys():
    """Return all surveys with their options for the admin UI."""

    supabase = db.get_supabase()
    surveys = supabase.table("surveys").select("*").execute().data or []
    for s in surveys:
        opts = (
            supabase.table("survey_options")
            .select("*")
            .eq("survey_id", s["id"])
            .execute()
            .data
            or []
        )
        s["options"] = sorted(opts, key=lambda o: o.get("order", 0))
    return {"surveys": surveys}

