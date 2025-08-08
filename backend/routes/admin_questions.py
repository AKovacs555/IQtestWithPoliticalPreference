import os
import logging
from typing import Optional
import asyncio
from math import ceil
from fastapi import APIRouter, Depends, HTTPException
from backend.deps.supabase_client import get_supabase_client
from backend.services.translator import translate_one
from .dependencies import require_admin
from pydantic import BaseModel


class ApproveAllRequest(BaseModel):
    approved: bool = True
    lang: str | None = None
    only_delta: bool = True  # if True, update only rows that actually need change


logger = logging.getLogger(__name__)

# Supported languages for translating questions from Japanese
TARGET_LANGS = ["en", "tr", "ru", "zh", "ko", "es", "fr", "it", "de", "ar"]

router = APIRouter(
    prefix="/admin/questions",
    tags=["admin-questions"],
)


@router.get("", dependencies=[Depends(require_admin)])
async def list_questions_no_slash():
    return await list_questions()


@router.get("/", dependencies=[Depends(require_admin)])
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


@router.get("/stats", dependencies=[Depends(require_admin)])
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


@router.post("/{group_id}/toggle_approved", dependencies=[Depends(require_admin)])
async def toggle_approved(group_id: str):
    supabase = get_supabase_client()
    records = (
        supabase.table("questions")
        .select("approved")
        .eq("group_id", group_id)
        .execute()
        .data
    )
    new_status = not records[0]["approved"] if records else True
    supabase.table("questions").update({"approved": new_status}).eq(
        "group_id", group_id
    ).execute()
    return {"group_id": group_id, "approved": new_status}


@router.post("/approve_batch", dependencies=[Depends(require_admin)])
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
        supabase.table("questions").update({"approved": payload["approved"]}).in_(
            "group_id", ids
        ).execute()
        return {"updated": len(ids), "approved": payload["approved"]}
    elif question_ids:
        supabase.table("questions").update({"approved": payload["approved"]}).in_(
            "id", question_ids
        ).execute()
        return {"updated": len(question_ids), "approved": payload["approved"]}
    else:
        raise HTTPException(status_code=400, detail="No IDs provided")


@router.post("/approve_all", dependencies=[Depends(require_admin)])
async def approve_all(payload: ApproveAllRequest):
    """
    Approve or unapprove all matching questions.
    If `lang` is provided, select the affected groups in that language and
    apply the change to ALL languages for those groups. If `lang` is None,
    apply the change to all rows.
    """
    supabase = get_supabase_client()

    def chunk(xs: list[str], n: int = 500):
        for i in range(0, len(xs), n):
            yield xs[i:i+n]

    # Case 1: a language is specified -> update all languages for those groups
    if payload.lang:
        sel_groups = supabase.table("questions").select("group_id").eq("lang", payload.lang)
        if payload.only_delta:
            sel_groups = sel_groups.is_("approved", not payload.approved)
        rows = sel_groups.execute().data or []
        group_ids = sorted({r.get("group_id") for r in rows if r.get("group_id")})
        if not group_ids:
            return {"updated": 0, "approved": payload.approved, "lang": payload.lang, "groups": 0}

        # Count rows that will actually change across all languages
        count_q = supabase.table("questions").select("id", count="exact").in_("group_id", group_ids)
        if payload.only_delta:
            count_q = count_q.is_("approved", not payload.approved)
        target_count = (count_q.execute().count) or 0

        # Update in batches across all languages for the selected groups
        for ids in chunk(group_ids):
            upd = supabase.table("questions").in_("group_id", ids)
            if payload.only_delta:
                upd = upd.is_("approved", not payload.approved)
            upd.update({"approved": payload.approved}).execute()

        return {"updated": target_count, "approved": payload.approved, "lang": payload.lang, "groups": len(group_ids)}

    # Case 2: no language specified -> global update
    sel = supabase.table("questions").select("id", count="exact")
    if payload.only_delta:
        sel = sel.is_("approved", not payload.approved)
    target_count = (sel.execute().count) or 0
    upd = supabase.table("questions")
    if payload.only_delta:
        upd = upd.is_("approved", not payload.approved)
    upd.update({"approved": payload.approved}).execute()
    return {"updated": target_count, "approved": payload.approved, "lang": None}


@router.post("/unapprove_all", dependencies=[Depends(require_admin)])
async def unapprove_all(payload: ApproveAllRequest):
    payload.approved = False
    return await approve_all(payload)


@router.put("/{question_id}", dependencies=[Depends(require_admin)])
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
        base = {
            "prompt": payload["question"],
            "options": payload["options"],
            "answer_index": payload["answer"],
            "explanation": payload.get("explanation", ""),
        }
        tasks = [translate_one(base, "ja", lang) for lang in TARGET_LANGS]
        results = await asyncio.gather(*tasks)
        for lang, translated in zip(TARGET_LANGS, results):
            update = {
                "question": translated["prompt"],
                "options": translated["options"],
                "answer": translated["answer_index"],
                "irt_a": payload["irt_a"],
                "irt_b": payload["irt_b"],
                "image_prompt": payload.get("image_prompt"),
                "image": payload.get("image"),
            }
            supabase.table("questions").update(update).eq(
                "group_id", record["group_id"]
            ).eq("lang", lang).execute()

    return {"updated": True}


@router.delete("/{question_id}", dependencies=[Depends(require_admin)])
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
        supabase.table("questions").delete().eq(
            "group_id", record["group_id"]
        ).execute()
    else:
        supabase.table("questions").delete().eq("id", question_id).execute()
    return {"deleted": True}


@router.post("/delete_batch", dependencies=[Depends(require_admin)])
async def delete_questions_batch(ids: list[int]):
    if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
        raise HTTPException(status_code=400, detail="ids must be list of ints")
    supabase = get_supabase_client()
    supabase.table("questions").delete().in_("id", ids).execute()
    return {"deleted": len(ids)}


@router.post("/delete_all", dependencies=[Depends(require_admin)])
async def delete_all_questions():
    supabase = get_supabase_client()
    supabase.table("questions").delete().neq("id", 0).execute()
    return {"deleted_all": True}
