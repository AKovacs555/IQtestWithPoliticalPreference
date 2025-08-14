from __future__ import annotations

"""Administrative survey management endpoints.

This module exposes CRUD operations for surveys and their items. All routes
require the requesting user to be an admin. Writes are performed using the
service-role Supabase client to ensure the appropriate privileges.

The Supabase python client does not currently expose explicit transaction
support. Survey creation therefore performs the survey insert followed by a
bulk insert of items. If the second step fails, the survey would remain
without items. This is acceptable for the current admin UI but could be
revisited with a SQL function for true atomicity in the future.
"""

from datetime import datetime
from typing import Literal
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.routes.dependencies import require_admin
from backend.db import insert_attempt_ledger


router = APIRouter(
    prefix="/admin/surveys",
    tags=["admin-surveys"],
    dependencies=[Depends(require_admin)],
)


def _admin_client():
    """Return the service-role Supabase client.

    Imported lazily to avoid requiring environment variables during module
    import time. Tests that do not exercise these routes therefore do not need
    Supabase credentials configured.
    """

    from backend.core.supabase_admin import supabase_admin  # type: ignore

    return supabase_admin


def grant_free_attempts(countries: list[str]) -> None:
    """Grant a free attempt to all users in ``countries`` via the ledger."""

    if not countries:
        return
    supabase = _admin_client()
    rows = (
        supabase.table("app_users")
        .select("hashed_id")
        .in_("nationality", countries)
        .execute()
        .data
    )
    for r in rows or []:
        insert_attempt_ledger(r.get("hashed_id"), 1, "ad")


SUPPORTED_LANGS = [
    "en",
    "ja",
    "ko",
    "zh",
    "es",
    "de",
    "fr",
    "pt",
    "ru",
    "ar",
    "id",
    "tr",
    "it",
    "pl",
    "nl",
    "vi",
]


def _normalize_lang(lang: str | None) -> str:
    """Return a supported lowercase language code or ``en``."""

    if not lang:
        return "en"
    lang = lang.lower()
    return lang if lang in SUPPORTED_LANGS else "en"


def _build_item_rows(survey_id: str, items: list[SurveyItemIn], lang: str):
    """Create fully-populated survey item rows for bulk insert."""

    rows: list[dict] = []
    pos = 1
    for it in items:
        text = (it.body or it.label or "").strip()
        if not text:
            continue
        rows.append(
            {
                "survey_id": survey_id,
                "position": pos,
                "body": text,
                "label": text,
                "choices": json.dumps([]),
                "is_exclusive": bool(it.is_exclusive),
                "is_active": True,
                "page": 1,
                "language": lang,
                "translation_language": lang,
            }
        )
        pos += 1
    return rows


class SurveyItemIn(BaseModel):
    """Input model for a survey item.

    Historically the admin UI used ``label`` for the text of a choice.
    The database, however, expects the field to be named ``body``.  Both
    fields are therefore accepted with ``body`` taking precedence.
    """

    label: str | None = None
    body: str | None = None
    is_exclusive: bool = False


class SurveyIn(BaseModel):
    """Input model for creating a survey with its items."""

    title: str
    question: str
    lang: str = "en"
    choice_type: Literal["sa", "ma"] = "sa"
    country_codes: list[str] = []
    items: list[SurveyItemIn]
    language: str | None = None


class SurveyUpdate(SurveyIn):
    """Model for updating a survey."""

    is_active: bool = True


@router.post("/")
async def create_survey(payload: SurveyIn):
    """Create a new survey along with its items."""

    supabase_admin = _admin_client()
    survey_lang = _normalize_lang(payload.language or payload.lang)
    payload_dict = payload.dict()
    survey_data = {
        "title": payload_dict.get("title"),
        "question": payload_dict.get("question"),
        "lang": survey_lang,
        "choice_type": payload_dict.get("choice_type"),
        "country_codes": payload_dict.get("country_codes"),
        "language": survey_lang,
    }
    res = supabase_admin.table("surveys").insert(survey_data, returning="representation").execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="failed to insert survey")
    survey_id = res.data[0]["id"]

    item_rows = _build_item_rows(survey_id, payload.items, survey_lang)
    if item_rows:
        supabase_admin.table("survey_items").insert(item_rows, returning="minimal").execute()

    return {"id": survey_id}


@router.post("", include_in_schema=False)
async def create_survey_alias(payload: SurveyIn):
    """Alias to allow posting without trailing slash."""
    return await create_survey(payload)


@router.get("/")
async def list_surveys():
    """Return surveys with their associated items, newest first."""

    supabase = _admin_client()
    surveys = (
        supabase.table("surveys")
        .select("*")
        .is_("deleted_at", "null")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    ids = [s["id"] for s in surveys]
    items_by_survey: dict[str, list[dict]] = {sid: [] for sid in ids}
    if ids:
        items = (
            supabase.table("survey_items")
            .select("*")
            .in_("survey_id", ids)
            .order("position")
            .execute()
            .data
            or []
        )
        for item in items:
            items_by_survey[item["survey_id"]].append(item)
    for s in surveys:
        s["items"] = items_by_survey.get(s["id"], [])
    return {"surveys": surveys}


@router.get("", include_in_schema=False)
async def list_surveys_alias():
    """Alias to allow getting without trailing slash."""
    return await list_surveys()


@router.put("/{survey_id}")
async def update_survey(survey_id: str, payload: SurveyUpdate):
    """Update survey fields and replace its items."""

    supabase = _admin_client()
    survey_lang = _normalize_lang(payload.language or payload.lang)
    data = {
        "title": payload.title,
        "question": payload.question,
        "lang": survey_lang,
        "choice_type": payload.choice_type,
        "country_codes": payload.country_codes,
        "is_active": payload.is_active,
        "language": survey_lang,
    }
    res_update = supabase.table("surveys").update(data).eq("id", survey_id).execute()
    if getattr(res_update, "error", None):
        raise HTTPException(status_code=500, detail=str(res_update.error))

    res_delete = supabase.table("survey_items").delete().eq("survey_id", survey_id).execute()
    if getattr(res_delete, "error", None):
        raise HTTPException(status_code=500, detail=str(res_delete.error))
    item_rows = _build_item_rows(survey_id, payload.items, survey_lang)
    if item_rows:
        res_items = supabase.table("survey_items").insert(item_rows).execute()
        if getattr(res_items, "error", None):
            raise HTTPException(status_code=500, detail=str(res_items.error))

    return {"updated": True}


@router.delete("/{survey_id}")
async def delete_survey(survey_id: str):
    """Soft-delete a survey by marking it inactive and setting deleted_at."""

    supabase = _admin_client()
    res = (
        supabase.table("surveys")
        .update({
            "deleted_at": datetime.utcnow().isoformat(),
            "is_active": False,
        })
        .eq("id", survey_id)
        .execute()
    )
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=str(res.error))
    return {"deleted": True}

