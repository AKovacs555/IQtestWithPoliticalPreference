from fastapi import APIRouter, Body, Depends, HTTPException, Response

from backend.routes.dependencies import require_admin
from backend.core.supabase_admin import supabase_admin
from backend import db

router = APIRouter(
    prefix="/admin/surveys",
    tags=["admin-surveys"],
    dependencies=[Depends(require_admin)],
)


def _norm_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return list(v)


def grant_free_attempts(countries: list[str]) -> None:  # pragma: no cover - legacy hook
    if not countries:
        return
    supabase = db.get_supabase()
    supabase.table("app_users").select("hashed_id").execute()


@router.post("/")
def create_survey(payload: dict = Body(...)):
    question_text = (
        payload.get("question_text")
        or payload.get("question")
        or payload.get("statement")
        or ""
    )
    if not question_text.strip():
        raise HTTPException(400, "question_text required")

    lang = payload.get("lang") or payload.get("language") or ""
    target_countries = _norm_list(
        payload.get("target_countries") or payload.get("nationalities")
    )
    target_genders = _norm_list(payload.get("target_genders"))
    survey_type = payload.get("type") or payload.get("selection")
    if survey_type not in {"sa", "ma"}:
        raise HTTPException(400, "type must be 'sa' or 'ma'")
    status = payload.get("status") or "approved"

    row = {
        "title": payload.get("title", ""),
        "question_text": question_text,
        "lang": lang,
        "target_countries": target_countries,
        "target_genders": target_genders,
        "type": survey_type,
        "status": status,
        "is_active": True,
    }
    res = supabase_admin.table("surveys").insert(row).execute()
    if not res.data:
        raise HTTPException(500, "failed to insert survey")
    new_id = res.data[0]["id"]

    items_in = payload.get("items") or payload.get("choices") or []
    item_rows = []
    for idx, it in enumerate(items_in):
        if isinstance(it, str):
            text = it.strip()
            exclusive = False
        else:
            text = (it.get("body") or it.get("text") or "").strip()
            exclusive = bool(
                it.get("is_exclusive")
                or it.get("isExclusive")
                or it.get("exclusive")
                or it.get("locks_others")
            )
        if not text:
            continue
        item_rows.append(
            {
                "survey_id": new_id,
                "position": idx + 1,
                "body": text,
                "is_exclusive": exclusive,
                "language": row["lang"],
                "is_active": True,
            }
        )
    if item_rows:
        supabase_admin.table("survey_items").insert(item_rows).execute()
    return {"id": new_id}


@router.put("/{survey_id}")
def update_survey(survey_id: str, payload: dict = Body(...)):
    question_text = (
        payload.get("question_text")
        or payload.get("question")
        or payload.get("statement")
        or ""
    )
    if not question_text.strip():
        raise HTTPException(400, "question_text required")

    lang = payload.get("lang") or payload.get("language") or ""
    target_countries = _norm_list(
        payload.get("target_countries") or payload.get("nationalities")
    )
    target_genders = _norm_list(payload.get("target_genders"))
    survey_type = payload.get("type") or payload.get("selection")
    if survey_type not in {"sa", "ma"}:
        raise HTTPException(400, "type must be 'sa' or 'ma'")
    status = payload.get("status") or "approved"

    data = {
        "title": payload.get("title", ""),
        "question_text": question_text,
        "lang": lang,
        "target_countries": target_countries,
        "target_genders": target_genders,
        "type": survey_type,
        "status": status,
        "is_active": payload.get("is_active", True),
    }
    supabase_admin.table("surveys").update(data).eq("id", survey_id).execute()
    supabase_admin.table("survey_items").delete().eq("survey_id", survey_id).execute()

    items_in = payload.get("items") or payload.get("choices") or []
    item_rows = []
    for idx, it in enumerate(items_in):
        if isinstance(it, str):
            text = it.strip()
            exclusive = False
        else:
            text = (it.get("body") or it.get("text") or "").strip()
            exclusive = bool(
                it.get("is_exclusive")
                or it.get("isExclusive")
                or it.get("exclusive")
                or it.get("locks_others")
            )
        if not text:
            continue
        item_rows.append(
            {
                "survey_id": survey_id,
                "position": idx + 1,
                "body": text,
                "is_exclusive": exclusive,
                "language": lang,
                "is_active": True,
            }
        )
    if item_rows:
        supabase_admin.table("survey_items").insert(item_rows).execute()
    return {"id": survey_id}


@router.get("/")
def list_surveys():
    res = supabase_admin.table("surveys").select(
        "id,title,question_text,lang,target_countries,target_genders,type,status"
    ).execute()
    surveys = res.data or []
    for s in surveys:
        items = (
            supabase_admin.table("survey_items")
            .select("id,survey_id,position,body,is_exclusive")
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
