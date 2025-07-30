import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from backend.deps.supabase_client import get_supabase_client

router = APIRouter(prefix="/admin/questions", tags=["admin-questions"])


def check_admin(admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    expected = os.environ.get("ADMIN_TOKEN")
    if expected is None or admin_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/", dependencies=[Depends(check_admin)])
async def list_questions():
    supabase = get_supabase_client()
    resp = supabase.table("questions").select("*").execute()
    return resp.data


@router.put("/{question_id}", dependencies=[Depends(check_admin)])
async def update_question(question_id: int, payload: dict):
    if not isinstance(payload.get("options"), list) or len(payload["options"]) != 4:
        raise HTTPException(status_code=400, detail="Options must be a list of 4 items")
    supabase = get_supabase_client()
    data = {
        "question": payload["question"],
        "options": payload["options"],
        "answer": payload["answer"],
        "irt_a": payload["irt_a"],
        "irt_b": payload["irt_b"],
        "image_prompt": payload.get("image_prompt"),
    }
    resp = (
        supabase.table("questions").update(data).eq("id", question_id).execute()
    )
    return resp.data


@router.delete("/{question_id}", dependencies=[Depends(check_admin)])
async def delete_question(question_id: int):
    supabase = get_supabase_client()
    supabase.table("questions").delete().eq("id", question_id).execute()
    return {"deleted": True}
