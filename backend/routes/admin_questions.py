import os
import logging
from typing import Optional
import asyncio
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Header
from backend.deps.supabase_client import get_supabase_client
from backend.utils.translation import translate_question

logger = logging.getLogger(__name__)

# Supported languages for translating questions from Japanese
TARGET_LANGS = ["en", "tr", "ru", "zh", "ko", "es", "fr", "it", "de", "ar"]

router = APIRouter(prefix="/admin/questions", tags=["admin-questions"])


def check_admin(admin_key: Optional[str] = Header(None, alias="X-Admin-Api-Key")):
    """
    Validate the provided admin API key against environment variables.
    Accepts either ADMIN_API_KEY or (for backward compatibility) ADMIN_TOKEN.
    Raises 500 if neither is configured, and 401 if the key is wrong.
    """
    expected_new = os.environ.get("ADMIN_API_KEY")
    expected_old = os.environ.get("ADMIN_TOKEN")
    expected = expected_new or expected_old
    if expected is None:
        logging.error("No ADMIN_API_KEY or ADMIN_TOKEN is set in the environment.")
        raise HTTPException(
            status_code=500, detail="Server misconfigured: missing admin key"
        )
    if admin_key != expected:
        logging.warning(
            f"Invalid admin key provided: {admin_key[:4]}… (expected length {len(expected)})"
        )
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("", dependencies=[Depends(check_admin)])
async def list_questions_no_slash():
    return await list_questions()


@router.get("/", dependencies=[Depends(check_admin)])
async def list_questions(lang: Optional[str] = None):
    supabase = get_supabase_client()
    try:
        query = supabase.table("questions").select("*")
        if lang:
            query = query.eq("lang", lang)
        resp = query.execute()
        return resp.data
    except Exception as e:
        logger.error("Error fetching questions from Supabase: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch questions")


@router.get("/stats", dependencies=[Depends(check_admin)])
async def question_stats():
    supabase = get_supabase_client()
    records = (
        supabase.table("questions")
        .select("lang, irt_b")
        .eq("approved", True)
        .execute()
        .data
    )

    stats: dict[str, dict[str, int]] = {}
    for r in records:
        lang = r.get("lang")
        irt_b = r.get("irt_b")
        if lang not in stats:
            stats[lang] = {"total": 0, "easy": 0, "medium": 0, "hard": 0}
        stats[lang]["total"] += 1
        if irt_b is None:
            diff = "medium"
        elif irt_b < -0.33:
            diff = "easy"
        elif irt_b < 0.33:
            diff = "medium"
        else:
            diff = "hard"
        stats[lang][diff] += 1

    num_questions = int(os.getenv("NUM_QUESTIONS", "20"))
    thresholds = {
        "easy": ceil(num_questions * 0.3),
        "medium": ceil(num_questions * 0.4),
        "hard": ceil(num_questions * 0.3),
    }

    result = {}
    for lang, counts in stats.items():
        sufficient = {
            diff: counts.get(diff, 0) >= threshold
            for diff, threshold in thresholds.items()
        }
        result[lang] = {**counts, "sufficient": sufficient}

    return result


@router.post("/{group_id}/toggle_approved", dependencies=[Depends(check_admin)])
async def toggle_approved(group_id: str):
    supabase = get_supabase_client()
    records = (
        supabase.table("questions").select("approved").eq("group_id", group_id).execute().data
    )
    new_status = not records[0]["approved"] if records else True
    supabase.table("questions").update({"approved": new_status}).eq("group_id", group_id).execute()
    return {"group_id": group_id, "approved": new_status}


@router.post("/approve_batch", dependencies=[Depends(check_admin)])
async def approve_batch(payload: dict):
    """
    Bulk approve or disapprove questions.
    Expects JSON body: {"group_ids": ["uuid1", "uuid2"], "approved": true}
    or, alternatively, {"ids": [1,2,3], "approved": true} to update by question IDs.
    """
    ids = payload.get("group_ids") or []
    question_ids = payload.get("ids") or []
    supabase = get_supabase_client()
    if ids:
        supabase.table("questions").update({"approved": payload["approved"]}).in_("group_id", ids).execute()
        return {"updated": len(ids), "approved": payload["approved"]}
    elif question_ids:
        supabase.table("questions").update({"approved": payload["approved"]}).in_("id", question_ids).execute()
        return {"updated": len(question_ids), "approved": payload["approved"]}
    else:
        raise HTTPException(status_code=400, detail="No IDs provided")


@router.put("/{question_id}", dependencies=[Depends(check_admin)])
async def update_question(question_id: int, payload: dict):
    if not isinstance(payload.get("options"), list) or len(payload["options"]) != 4:
        raise HTTPException(status_code=400, detail="Options must be a list of 4 items")
    supabase = get_supabase_client()
    record = (
        supabase.table("questions")
        .select("group_id,lang")
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

    if record.get("lang") == "ja":
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
            supabase.table("questions").update(update).eq("group_id", record["group_id"]).eq("lang", lang).execute()

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
