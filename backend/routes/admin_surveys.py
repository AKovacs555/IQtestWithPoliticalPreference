import uuid
from fastapi import APIRouter, Depends

from backend.routes.dependencies import require_admin
from backend.deps.supabase_client import get_supabase_client

router = APIRouter(
    prefix="/admin/surveys",
    tags=["admin-surveys"],
    dependencies=[Depends(require_admin)],
)


def grant_free_tests(countries: list[str]) -> None:
    if not countries:
        return
    supabase = get_supabase_client()
    supabase.table("app_users").update({"free_tests": "free_tests + 1"}).in_("nationality", countries).execute()


@router.get("/")
async def list_surveys():
    supabase = get_supabase_client()
    res = supabase.table("surveys").select("*").execute()
    return {"surveys": res.data or []}


@router.post("/")
async def create_survey(payload: dict):
    supabase = get_supabase_client()
    data = {
        "id": str(uuid.uuid4()),
        "title": payload.get("title"),
        "lang": payload.get("lang", "ja"),
        "status": payload.get("status", "draft"),
    }
    res = supabase.table("surveys").insert(data).execute()
    return res.data[0]


@router.put("/{survey_id}")
async def update_survey(survey_id: str, payload: dict):
    supabase = get_supabase_client()
    data = {k: v for k, v in payload.items() if k in {"title", "lang", "status"}}
    supabase.table("surveys").update(data).eq("id", survey_id).execute()
    return {"updated": True}


@router.delete("/{survey_id}")
async def delete_survey(survey_id: str):
    supabase = get_supabase_client()
    supabase.table("surveys").delete().eq("id", survey_id).execute()
    return {"deleted": True}


@router.get("/{survey_id}/items")
async def list_items(survey_id: str):
    supabase = get_supabase_client()
    res = (
        supabase.table("survey_items")
        .select("*")
        .eq("survey_id", survey_id)
        .order("order_no")
        .execute()
    )
    return {"items": res.data or []}


@router.post("/{survey_id}/items")
async def create_item(survey_id: str, payload: dict):
    supabase = get_supabase_client()
    data = {
        "id": str(uuid.uuid4()),
        "survey_id": survey_id,
        "body": payload.get("body"),
        "choices": payload.get("choices", []),
        "order_no": payload.get("order_no", 0),
        "lang": payload.get("lang", "ja"),
        "is_active": payload.get("is_active", True),
    }
    res = supabase.table("survey_items").insert(data).execute()
    return res.data[0]


@router.put("/items/{item_id}")
async def update_item(item_id: str, payload: dict):
    supabase = get_supabase_client()
    data = {k: v for k, v in payload.items() if k in {"body", "choices", "order_no", "lang", "is_active"}}
    supabase.table("survey_items").update(data).eq("id", item_id).execute()
    return {"updated": True}


@router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    supabase = get_supabase_client()
    supabase.table("survey_items").delete().eq("id", item_id).execute()
    return {"deleted": True}
