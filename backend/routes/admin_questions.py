import os
import logging
from typing import Optional
from math import ceil
from fastapi import APIRouter, Depends, HTTPException
from backend.deps.supabase_client import get_supabase_client
from backend.db import (
    get_group_key_by_id,
    update_question_group,
    approve_question_group,
    delete_question_group,
)
from .dependencies import require_admin
from pydantic import BaseModel


class ApproveAllRequest(BaseModel):
    approved: bool = True
    lang: str | None = None
    scope: str = "lang"  # "lang" or "group"
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
    """Toggle approval for a group.

    Deprecated: prefer POST /{id}/approve or /{id}/unapprove which operate on
    ``orig_id`` groups.
    """
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


# ---------------------------------------------------------------------------
# New group-aware approval endpoints
# ---------------------------------------------------------------------------


@router.post("/{question_id}/approve", dependencies=[Depends(require_admin)])
async def approve_question(question_id: str):
    """Approve all translations for the given question id."""
    group_key = get_group_key_by_id(str(question_id))
    if not group_key:
        raise HTTPException(status_code=404, detail="Question not found")
    approve_question_group(group_key, True)
    return {"group_key": group_key, "approved": True}


@router.post("/{question_id}/unapprove", dependencies=[Depends(require_admin)])
async def unapprove_question(question_id: str):
    group_key = get_group_key_by_id(str(question_id))
    if not group_key:
        raise HTTPException(status_code=404, detail="Question not found")
    approve_question_group(group_key, False)
    return {"group_key": group_key, "approved": False}


@router.post("/approve_batch", dependencies=[Depends(require_admin)])
async def approve_batch(payload: dict):
    """Bulk approve or disapprove questions.

    Deprecated: use ``/approve_all`` with ``scope="group"`` instead.
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
    """Bulk approve or unapprove questions.

    When ``scope`` is ``lang`` (default), update only rows in the specified
    language. When ``scope`` is ``group``, fetch all distinct ``orig_id`` values
    for the selection and apply the change to every translation in each group.
    Returns the updated rows for UI refresh.
    """

    supabase = get_supabase_client()

    if payload.scope == "group":
        sel = supabase.table("questions").select("orig_id")
        if payload.lang:
            sel = sel.eq("lang", payload.lang)
        if payload.only_delta:
            sel = sel.is_("approved", not payload.approved)
        rows = sel.execute().data or []
        group_keys = sorted({r.get("orig_id") for r in rows if r.get("orig_id")})
        if group_keys:
            upd = supabase.table("questions").update({"approved": payload.approved}).in_("orig_id", group_keys)
            if payload.only_delta:
                upd = upd.is_("approved", not payload.approved)
            upd.execute()
            updated = supabase.table("questions").select("*").in_("orig_id", group_keys).execute().data or []
        else:
            updated = []
        return {"updated": len(updated), "approved": payload.approved, "rows": updated}

    # scope == "lang"
    pre = supabase.table("questions").select("id")
    if payload.lang:
        pre = pre.eq("lang", payload.lang)
    if payload.only_delta:
        pre = pre.is_("approved", not payload.approved)
    pre_rows = pre.execute().data or []
    ids = [r.get("id") for r in pre_rows if r.get("id")]
    upd = supabase.table("questions").update({"approved": payload.approved})
    if ids:
        upd = upd.in_("id", ids)
    elif payload.lang:
        upd = upd.eq("lang", payload.lang)
    upd.execute()
    if ids:
        rows = (
            supabase.table("questions").select("*").in_("id", ids).execute().data or []
        )
    else:
        rows = []
    return {"updated": len(rows), "approved": payload.approved, "rows": rows}


@router.post("/unapprove_all", dependencies=[Depends(require_admin)])
async def unapprove_all(payload: ApproveAllRequest):
    payload.approved = False
    return await approve_all(payload)


@router.put("/{question_id}", dependencies=[Depends(require_admin)])
async def update_question(
    question_id: str, payload: dict, apply_text_to_all: bool = False
):
    """Update a question across all translations.

    Deprecated: the former single-language translation flow has been replaced by
    group-wide updates. Set ``apply_text_to_all`` to True to overwrite text
    fields in all languages.
    """

    group_key = get_group_key_by_id(str(question_id))
    if not group_key:
        raise HTTPException(status_code=404, detail="Question not found")

    TEXT_FIELDS = ["question", "A1", "A2", "A3", "A4", "explanation_text"]
    update_question_group(group_key, payload, TEXT_FIELDS, apply_text_to_all)
    return {"updated": True, "group_key": group_key}


@router.delete("/{question_id}", dependencies=[Depends(require_admin)])
async def delete_question(question_id: str):
    group_key = get_group_key_by_id(str(question_id))
    if not group_key:
        raise HTTPException(status_code=404, detail="Question not found")
    delete_question_group(group_key)
    return {"deleted": True, "group_key": group_key}


@router.post("/delete_batch", dependencies=[Depends(require_admin)])
async def delete_questions_batch(ids: list[int]):
    """Delete questions by id.

    Deprecated: prefer DELETE /admin/questions/{id} which removes all
    translations for a group.
    """
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
