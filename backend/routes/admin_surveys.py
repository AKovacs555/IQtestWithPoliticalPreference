from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from backend.routes.dependencies import require_admin
from backend.core.supabase_admin import supabase_admin
from backend import db

router = APIRouter(
    prefix="/admin/surveys",
    tags=["admin-surveys"],
    dependencies=[Depends(require_admin)],
)

def grant_free_attempts(countries: list[str]) -> None:  # pragma: no cover - legacy hook
    if not countries:
        return
    supabase = db.get_supabase()
    supabase.table("app_users").select("hashed_id").execute()

class SurveyPayload(BaseModel):
    title: str
    question_text: str
    lang: str
    allowed_countries: List[str] = Field(default_factory=list)
    selection: Literal["sa", "ma"]
    exclusive_indexes: List[int] = Field(default_factory=list)
    choices: List[str]

@router.post("/")
def create_survey(payload: SurveyPayload):
    if not payload.question_text.strip():
        raise HTTPException(400, "question_text required")
    if len(payload.choices) < 2:
        raise HTTPException(400, "at least two choices required")
    row = {
        "title": payload.title,
        "question_text": payload.question_text,
        "lang": payload.lang,
        "allowed_countries": payload.allowed_countries,
        "is_single_choice": payload.selection == "sa",
        "status": "approved",
        "is_active": True,
    }
    res = supabase_admin.table("surveys").insert(row).select("id").single().execute()
    if not res.data:
        raise HTTPException(500, "failed to insert survey")
    survey_id = res.data["id"]
    items = [
        {
            "survey_id": survey_id,
            "position": i + 1,
            "statement": text,
            "is_exclusive": i in payload.exclusive_indexes,
        }
        for i, text in enumerate(payload.choices)
    ]
    if items:
        supabase_admin.table("survey_items").insert(items, returning="minimal").execute()
    return {"id": survey_id}

@router.put("/{survey_id}")
def update_survey(survey_id: str, payload: SurveyPayload):
    if not payload.question_text.strip():
        raise HTTPException(400, "question_text required")
    if len(payload.choices) < 2:
        raise HTTPException(400, "at least two choices required")
    data = {
        "title": payload.title,
        "question_text": payload.question_text,
        "lang": payload.lang,
        "allowed_countries": payload.allowed_countries,
        "is_single_choice": payload.selection == "sa",
    }
    supabase_admin.table("surveys").update(data).eq("id", survey_id).execute()
    supabase_admin.table("survey_items").delete().eq("survey_id", survey_id).execute()
    items = [
        {
            "survey_id": survey_id,
            "position": i + 1,
            "statement": text,
            "is_exclusive": i in payload.exclusive_indexes,
        }
        for i, text in enumerate(payload.choices)
    ]
    if items:
        supabase_admin.table("survey_items").insert(items, returning="minimal").execute()
    return {"id": survey_id}

@router.get("/")
def list_surveys():
    res = supabase_admin.table("surveys").select(
        "id,title,question_text,lang,allowed_countries,is_single_choice,status,is_active"
    ).execute()
    surveys = res.data or []
    for s in surveys:
        items = (
            supabase_admin.table("survey_items")
            .select("id,survey_id,position,statement,is_exclusive")
            .eq("survey_id", s["id"])
            .order("position")
            .execute()
            .data
            or []
        )
        s["items"] = items
    return {"surveys": surveys}

@router.delete("/{survey_id}", status_code=204)
def delete_survey(survey_id: str):
    supabase_admin.table("surveys").delete().eq("id", survey_id).execute()
    return Response(status_code=204)
