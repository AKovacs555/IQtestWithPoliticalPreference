import os
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.db import get_surveys, insert_surveys, delete_survey
from backend.utils.translation import LANG_NAME_MAP, translate_survey

router = APIRouter(prefix="/admin/surveys", tags=["admin-surveys"])

logger = logging.getLogger(__name__)


def check_admin(admin_key: Optional[str] = Header(None, alias="X-Admin-Api-Key")):
    expected_new = os.environ.get("ADMIN_API_KEY")
    expected_old = os.environ.get("ADMIN_TOKEN")
    expected = expected_new or expected_old
    if expected is None:
        logger.error("No ADMIN_API_KEY or ADMIN_TOKEN is set in the environment.")
        raise HTTPException(status_code=500, detail="Server misconfigured: missing admin key")
    if admin_key != expected:
        logger.warning("Invalid admin key provided")
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/", dependencies=[Depends(check_admin)])
async def list_questions(lang: Optional[str] = None):
    data = get_surveys()
    grouped: dict[str, dict] = {}
    for q in data:
        gid = q.get("group_id")
        if lang and q.get("lang") == lang:
            grouped[gid] = q
        elif gid not in grouped:
            grouped[gid] = q
    return {"questions": list(grouped.values())}


@router.get("/languages", dependencies=[Depends(check_admin)])
async def get_languages():
    return {"languages": list(LANG_NAME_MAP.keys())}


@router.post("/", dependencies=[Depends(check_admin)])
async def create_question(payload: dict):
    base_lang = payload.get("lang")
    statement = payload.get("statement")
    options = payload.get("options")
    q_type = payload.get("type", "sa")
    exclusive = payload.get("exclusive_options", [])
    if not base_lang or not statement or not options:
        raise HTTPException(status_code=400, detail="Missing required fields")

    group_id = str(uuid.uuid4())
    rows = [
        {
            "group_id": group_id,
            "lang": base_lang,
            "statement": statement,
            "options": options,
            "type": q_type,
            "exclusive_options": exclusive,
            "lr": payload.get("lr", 0),
            "auth": payload.get("auth", 0),
        }
    ]

    for lang_code in LANG_NAME_MAP.keys():
        if lang_code == base_lang:
            continue
        translated_statement, translated_options = await translate_survey(statement, options, lang_code)
        rows.append(
            {
                "group_id": group_id,
                "lang": lang_code,
                "statement": translated_statement,
                "options": translated_options,
                "type": q_type,
                "exclusive_options": exclusive,
                "lr": payload.get("lr", 0),
                "auth": payload.get("auth", 0),
            }
        )

    insert_surveys(rows)
    return rows[0]


@router.put("/{group_id}", dependencies=[Depends(check_admin)])
async def update_question(group_id: str, payload: dict):
    base_lang = payload.get("lang")
    statement = payload.get("statement")
    options = payload.get("options")
    q_type = payload.get("type", "sa")
    exclusive = payload.get("exclusive_options", [])
    if not base_lang or not statement or not options:
        raise HTTPException(status_code=400, detail="Missing required fields")

    delete_survey(group_id)
    rows = [
        {
            "group_id": group_id,
            "lang": base_lang,
            "statement": statement,
            "options": options,
            "type": q_type,
            "exclusive_options": exclusive,
            "lr": payload.get("lr", 0),
            "auth": payload.get("auth", 0),
        }
    ]
    for lang_code in LANG_NAME_MAP.keys():
        if lang_code == base_lang:
            continue
        translated_statement, translated_options = await translate_survey(statement, options, lang_code)
        rows.append(
            {
                "group_id": group_id,
                "lang": lang_code,
                "statement": translated_statement,
                "options": translated_options,
                "type": q_type,
                "exclusive_options": exclusive,
                "lr": payload.get("lr", 0),
                "auth": payload.get("auth", 0),
            }
        )
    insert_surveys(rows)
    return rows[0]


@router.delete("/{group_id}", dependencies=[Depends(check_admin)])
async def delete_question(group_id: str):
    delete_survey(group_id)
    return {"deleted": True}
