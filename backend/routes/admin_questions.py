import os
import logging
from typing import Optional
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Header
from backend.deps.supabase_client import get_supabase_client
from backend.utils.translation import translate_question

logger = logging.getLogger(__name__)

# Supported languages for translating questions from Japanese
TARGET_LANGS = ["en", "tr", "ru", "zh", "ko", "es", "fr", "it", "de", "ar"]

router = APIRouter(prefix="/admin/questions", tags=["admin-questions"])


def check_admin(admin_key: Optional[str] = Header(None, alias="X-Admin-Api-Key")):
    expected = os.environ.get("ADMIN_API_KEY")
    if expected is None or admin_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/", dependencies=[Depends(check_admin)])
async def list_questions():
    supabase = get_supabase_client()
    try:
        resp = supabase.table("questions").select("*").execute()
        return resp.data
    except Exception as e:
        logger.error("Error fetching questions from Supabase: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch questions")


@router.post("/{group_id}/toggle_approved", dependencies=[Depends(check_admin)])
async def toggle_approved(group_id: str):
    supabase = get_supabase_client()
    records = (
        supabase.table("questions").select("approved").eq("group_id", group_id).execute().data
    )
    new_status = not records[0]["approved"] if records else True
    supabase.table("questions").update({"approved": new_status}).eq("group_id", group_id).execute()
    return {"group_id": group_id, "approved": new_status}


@router.put("/{question_id}", dependencies=[Depends(check_admin)])
async def update_question(question_id: int, payload: dict):
    if not isinstance(payload.get("options"), list) or len(payload["options"]) != 4:
        raise HTTPException(status_code=400, detail="Options must be a list of 4 items")
    supabase = get_supabase_client()
    record = (
        supabase.table("questions")
        .select("group_id,language")
        .eq("id", question_id)
        .single()
        .execute()
    ).data
    if not record:
        raise HTTPException(status_code=404, detail="Question not found")

    data = {
        "question": payload["question"],
        "options": payload["options"],
        "answer": payload["answer"],
        "irt_a": payload["irt_a"],
        "irt_b": payload["irt_b"],
        "image_prompt": payload.get("image_prompt"),
        "image": payload.get("image"),
    }
    supabase.table("questions").update(data).eq("id", question_id).execute()

    if record.get("language") == "ja":
        tasks = [
            translate_question(payload["question"], payload["options"], lang)
            for lang in TARGET_LANGS
        ]
        results = await asyncio.gather(*tasks)
        for lang, res in zip(TARGET_LANGS, results):
            q_trans, opts_trans = res
            update = {
                "question": q_trans,
                "options": opts_trans,
                "answer": payload["answer"],
                "irt_a": payload["irt_a"],
                "irt_b": payload["irt_b"],
                "image_prompt": payload.get("image_prompt"),
                "image": payload.get("image"),
            }
            supabase.table("questions").update(update).eq("group_id", record["group_id"]).eq("language", lang).execute()

    return {"updated": True}


@router.delete("/{question_id}", dependencies=[Depends(check_admin)])
async def delete_question(question_id: int):
    supabase = get_supabase_client()
    record = (
        supabase.table("questions")
        .select("group_id")
        .eq("id", question_id)
        .single()
        .execute()
    ).data
    if record and record.get("group_id"):
        supabase.table("questions").delete().eq("group_id", record["group_id"]).execute()
    else:
        supabase.table("questions").delete().eq("id", question_id).execute()
    return {"deleted": True}


@router.post("/delete_batch", dependencies=[Depends(check_admin)])
async def delete_questions_batch(ids: list[int]):
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        raise HTTPException(status_code=400, detail="ids must be list of ints")
    supabase = get_supabase_client()
    supabase.table("questions").delete().in_("id", ids).execute()
    return {"deleted": len(ids)}


@router.post("/delete_all", dependencies=[Depends(check_admin)])
async def delete_all_questions():
    supabase = get_supabase_client()
    supabase.table("questions").delete().neq("id", 0).execute()
    return {"deleted_all": True}
