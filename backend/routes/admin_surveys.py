import uuid
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends

from backend.deps.supabase_client import get_supabase_client
from backend.routes.dependencies import require_admin
from backend import db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/surveys", tags=["admin-surveys"])

# Pydantic models for request payloads
from pydantic import BaseModel

class SurveyItemPayload(BaseModel):
    body: str
    is_exclusive: bool = False
    lang: str

class SurveyPayload(BaseModel):
    title: str
    question_text: str
    type: str  # 'sa' or 'ma'
    lang: str
    target_countries: List[str]
    target_genders: List[str]
    items: List[SurveyItemPayload]

@router.get("", dependencies=[Depends(require_admin)])
async def list_surveys_no_slash():
    """List all surveys (with their choice items) for admin view."""
    return await list_surveys()

@router.get("/", dependencies=[Depends(require_admin)])
async def list_surveys(lang: str | None = None):
    supabase = get_supabase_client()
    try:
        # Fetch surveys with nested items (similar to db.get_surveys)
        select_expr = "id,title,question_text,lang,target_countries,target_genders,type,status,is_active,group_id,is_single_choice," \
                      "survey_items(id,position,body,is_exclusive,is_active)"
        query = supabase.from_("surveys").select(select_expr)
        if lang:
            query = query.eq("lang", lang)
        resp = query.execute()
        surveys = resp.data or []
        # Sort each survey's items by position for consistency
        for s in surveys:
            items = s.get("survey_items") or []
            items.sort(key=lambda it: it.get("position", 0))
            s["survey_items"] = items
        return {"surveys": surveys}
    except Exception as e:
        logger.error("Error fetching surveys: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch surveys")

@router.post("", dependencies=[Depends(require_admin)])
async def create_survey(payload: SurveyPayload):
    """Create a new survey (with its choice items)."""
    supabase = get_supabase_client()
    # Generate IDs for survey and group
    survey_id = str(uuid.uuid4())
    group_id = str(uuid.uuid4())
    survey_data = {
        "id": survey_id,
        "title": payload.title,
        "question_text": payload.question_text,
        "type": payload.type,
        "lang": payload.lang,
        "target_countries": payload.target_countries,
        "target_genders": payload.target_genders,
        "status": "draft",
        "is_active": True,
        "group_id": group_id,
        "is_single_choice": True if payload.type == "sa" else False,
    }
    # Prepare survey_items records
    item_rows = []
    for idx, item in enumerate(payload.items):
        row = {
            "survey_id": survey_id,
            "body": item.body,
            "is_exclusive": item.is_exclusive,
            "position": idx + 1,
            "language": item.lang if hasattr(item, "lang") else payload.lang,  # ensure field matches DB column
            "is_active": True,
        }
        # Set translation_language if applicable
        if row["language"] != "en":
            row["translation_language"] = "en"
        item_rows.append(row)
    try:
        supabase.from_("surveys").insert(survey_data).execute()
        if item_rows:
            supabase.from_("survey_items").insert(item_rows).execute()
    except Exception as e:
        logger.error("Failed to create survey: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create survey")
    return {"id": survey_id}

@router.put("/{survey_id}", dependencies=[Depends(require_admin)])
async def update_survey(survey_id: str, payload: SurveyPayload):
    """Update an existing survey (and replace its choice items)."""
    supabase = get_supabase_client()
    # Update survey core fields
    update_data = {
        "title": payload.title,
        "question_text": payload.question_text,
        "type": payload.type,
        "lang": payload.lang,
        "target_countries": payload.target_countries,
        "target_genders": payload.target_genders,
        "is_single_choice": True if payload.type == "sa" else False,
    }
    try:
        supabase.from_("surveys").update(update_data).eq("id", survey_id).execute()
    except Exception as e:
        logger.error("Failed to update survey %s: %s", survey_id, e)
        raise HTTPException(status_code=500, detail="Failed to update survey")
    # Re-create survey items
    item_rows = []
    for idx, item in enumerate(payload.items):
        row = {
            "survey_id": survey_id,
            "body": item.body,
            "is_exclusive": item.is_exclusive,
            "position": idx + 1,
            "language": item.lang if hasattr(item, "lang") else payload.lang,
            "is_active": True,
        }
        if row["language"] != "en":
            row["translation_language"] = "en"
        item_rows.append(row)
    try:
        supabase.from_("survey_items").delete().eq("survey_id", survey_id).execute()
        if item_rows:
            supabase.from_("survey_items").insert(item_rows).execute()
    except Exception as e:
        logger.error("Failed to replace survey items for %s: %s", survey_id, e)
        raise HTTPException(status_code=500, detail="Failed to update survey items")
    return {"id": survey_id, "updated": True}

@router.patch("/{survey_id}/status", dependencies=[Depends(require_admin)])
async def update_survey_status(survey_id: str, payload: dict):
    """Update survey status and activation state."""
    supabase = get_supabase_client()
    new_status = payload.get("status")
    is_active = payload.get("is_active", True)
    if not new_status:
        raise HTTPException(status_code=400, detail="Missing status")
    try:
        supabase.from_("surveys").update({"status": new_status, "is_active": is_active}).eq("id", survey_id).execute()
    except Exception as e:
        logger.error("Failed to update survey status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update status")
    return {"id": survey_id, "status": new_status, "is_active": is_active}

@router.delete("/{survey_id}", dependencies=[Depends(require_admin)])
async def delete_survey(survey_id: str):
    """Delete a survey and all its associated items."""
    supabase = get_supabase_client()
    try:
        # Remove any answers for this survey (if present)
        supabase.from_("survey_answers").delete().eq("survey_id", survey_id).execute()
        supabase.from_("survey_items").delete().eq("survey_id", survey_id).execute()
        supabase.from_("surveys").delete().eq("id", survey_id).execute()
    except Exception as e:
        logger.error("Failed to delete survey %s: %s", survey_id, e)
        raise HTTPException(status_code=500, detail="Failed to delete survey")
    return {"deleted": True}
