import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.db import (
    get_surveys,
    insert_surveys,
    update_survey,
    delete_survey,
    get_dashboard_default_survey,
    set_dashboard_default_survey,
)
from backend.services.translator import translate_one
from backend.deps.supabase_client import get_supabase_client
from .dependencies import require_admin


router = APIRouter(prefix="/admin/surveys", tags=["admin-surveys"])

logger = logging.getLogger(__name__)


# Language options should mirror those available to end users
LANGUAGES = ["ja", "en", "tr", "ru", "zh", "ko", "es", "fr", "it", "de", "ar"]
SUPPORTED_LANGUAGES = ["en", "ja", "es", "de", "it", "tr", "fr", "zh", "ko", "ar"]


def grant_free_tests(countries: list[str]) -> None:
    """Increment free test credits for users from given countries."""
    if not countries:
        return
    supabase = get_supabase_client()
    # Supabase Python client doesn't support increment directly, so use raw string
    supabase.table("users").update({"free_tests": "free_tests + 1"}).in_(
        "nationality", countries
    ).execute()


@router.get("/languages", dependencies=[Depends(require_admin)])
async def list_languages():
    """Return the available languages for survey creation."""
    return {"languages": LANGUAGES}


@router.get("/", dependencies=[Depends(require_admin)])
async def list_surveys(lang: str = "ja"):
    surveys = get_surveys(lang)
    return {"questions": surveys}


@router.post("/", dependencies=[Depends(require_admin)])
async def create_survey(payload: dict):
    group_id = str(uuid.uuid4())
    base_entry = {**payload, "group_id": group_id}
    rows = [base_entry]

    base_lang = payload.get("lang")
    if base_lang in SUPPORTED_LANGUAGES:
        for lang in SUPPORTED_LANGUAGES:
            if lang == base_lang:
                continue
            translated = await translate_one(
                {
                    "prompt": payload["statement"],
                    "options": payload["options"],
                    "answer_index": 0,
                    "explanation": "",
                },
                base_lang,
                lang,
            )
            rows.append(
                {
                    "group_id": group_id,
                    "lang": lang,
                    "statement": translated["prompt"],
                    "options": translated["options"],
                    "type": payload["type"],
                    "exclusive_options": payload["exclusive_options"],
                    "lr": payload.get("lr", 0),
                    "auth": payload.get("auth", 0),
                    "target_countries": payload.get("target_countries", []),
                }
            )

    insert_surveys(rows)
    grant_free_tests(payload.get("target_countries", []))
    return base_entry


@router.put("/{group_id}", dependencies=[Depends(require_admin)])
async def edit_survey(group_id: str, payload: dict):
    update_survey(group_id, payload["lang"], payload)

    base_lang = payload.get("lang")
    if base_lang in SUPPORTED_LANGUAGES:
        for lang in SUPPORTED_LANGUAGES:
            if lang == base_lang:
                continue
            translated = await translate_one(
                {
                    "prompt": payload["statement"],
                    "options": payload["options"],
                    "answer_index": 0,
                    "explanation": "",
                },
                base_lang,
                lang,
            )
            update_survey(
                group_id,
                lang,
                {
                    "statement": translated["prompt"],
                    "options": translated["options"],
                    "type": payload["type"],
                    "exclusive_options": payload["exclusive_options"],
                    "lr": payload.get("lr", 0),
                    "auth": payload.get("auth", 0),
                    "target_countries": payload.get("target_countries", []),
                },
            )
    return {"updated": True}


@router.delete("/{group_id}", dependencies=[Depends(require_admin)])
async def remove_survey(group_id: str):
    delete_survey(group_id)
    return {"deleted": True}


@router.get("/dashboard-default-survey", dependencies=[Depends(require_admin)])
async def get_dashboard_default():
    group_id = get_dashboard_default_survey()
    return {"group_id": group_id}


@router.post(
    "/dashboard-default-survey", dependencies=[Depends(require_admin)]
)
async def set_dashboard_default(payload: dict):
    set_dashboard_default_survey(payload.get("group_id"))
    return {"status": "ok"}
