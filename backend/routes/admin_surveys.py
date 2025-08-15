from fastapi import APIRouter, Body, Depends, HTTPException, Response

from backend.routes.dependencies import require_admin
from backend.core.supabase_admin import supabase_admin
from backend import db
import uuid
import logging
from backend.services.openai_client import translate_with_openai

logger = logging.getLogger(__name__)


# Supported languages for automatic translation
BASE_TARGET_LANGS = ["en", "tr", "ru", "zh", "ko", "es", "fr", "it", "de", "ar"]

LANG_DISPLAY = {
    "en": "English",
    "tr": "Turkish",
    "ru": "Russian",
    "zh": "Chinese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "de": "German",
    "ar": "Arabic",
    "ja": "Japanese",
}


def _build_prompt(src: str, tgt: str) -> str:
    return (
        "You are a professional translator. "
        "Translate the following text into {lang}. "
        "Return ONLY the translated text without extra commentary.\n\n"
        "=== SOURCE LANGUAGE TEXT ===\n{src}\n"
    ).format(lang=LANG_DISPLAY.get(tgt, tgt), src=src)

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


@router.post("/", status_code=201)
def create_survey(payload: dict = Body(...)):
    question_text = (
        payload.get("question_text")
        or payload.get("question")
        or payload.get("statement")
        or ""
    )
    if not question_text.strip():
        raise HTTPException(400, "question_text required")

    lang = payload.get("lang") or payload.get("language") or "en"
    target_countries = _norm_list(
        payload.get("target_countries") or payload.get("nationalities")
    )
    target_genders = _norm_list(payload.get("target_genders"))
    survey_type = payload.get("type") or payload.get("selection")
    if survey_type not in {"sa", "ma"}:
        raise HTTPException(400, "type must be 'sa' or 'ma'")
    status = payload.get("status") or "approved"
    is_single_choice = survey_type in ("sa", "single")

    group_id = payload.get("group_id") or str(uuid.uuid4())
    row = {
        "title": payload.get("title", ""),
        "question_text": question_text,
        "lang": lang,
        "target_countries": target_countries,
        "target_genders": target_genders,
        "type": survey_type,
        "status": status,
        "is_active": True,
        "group_id": group_id,
        "is_single_choice": is_single_choice,
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
                "language": lang,
                "is_active": True,
            }
        )
    if item_rows:
        supabase_admin.table("survey_items").insert(item_rows).execute()

    # Determine target languages for translation
    targets = list(BASE_TARGET_LANGS)
    if lang != "ja":
        targets.append("ja")
    if lang in targets:
        targets.remove(lang)

    # Prepare base texts for translation
    base_title = row.get("title", "")
    base_items = item_rows

    for tgt in targets:
        try:
            translated_question = translate_with_openai(_build_prompt(question_text, tgt))
            translated_title = (
                translate_with_openai(_build_prompt(base_title, tgt)) if base_title else ""
            )
            translated_options = [
                translate_with_openai(_build_prompt(it["body"], tgt)) for it in base_items
            ]
        except Exception as exc:  # pragma: no cover - network failures
            logger.error("Translation %s failed for survey %s: %s", tgt, group_id, exc, exc_info=True)
            continue

        trans_row = {
            "title": translated_title,
            "question_text": translated_question,
            "lang": tgt,
            "target_countries": target_countries,
            "target_genders": target_genders,
            "type": survey_type,
            "status": status,
            "is_active": True,
            "group_id": group_id,
            "is_single_choice": is_single_choice,
        }
        res_t = supabase_admin.table("surveys").insert(trans_row).execute()
        if not (res_t.data):
            continue
        new_tid = res_t.data[0]["id"]
        trans_items = []
        for base_it, body in zip(base_items, translated_options):
            trans_items.append(
                {
                    "survey_id": new_tid,
                    "position": base_it["position"],
                    "body": body,
                    "is_exclusive": base_it.get("is_exclusive", False),
                    "language": tgt,
                    "is_active": True,
                }
            )
        if trans_items:
            supabase_admin.table("survey_items").insert(trans_items).execute()

    return {"id": new_id, "group_id": group_id}


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

    lang = payload.get("lang") or payload.get("language") or "en"
    target_countries = _norm_list(
        payload.get("target_countries") or payload.get("nationalities")
    )
    target_genders = _norm_list(payload.get("target_genders"))
    survey_type = payload.get("type") or payload.get("selection")
    if survey_type not in {"sa", "ma"}:
        raise HTTPException(400, "type must be 'sa' or 'ma'")
    status = payload.get("status") or "approved"
    is_single_choice = survey_type in ("sa", "single")

    # Determine group_id and existing translations
    gid_resp = (
        supabase_admin.table("surveys")
        .select("group_id,lang")
        .eq("id", survey_id)
        .execute()
    )
    if not gid_resp.data:
        raise HTTPException(404, "survey not found")
    group_id = gid_resp.data[0]["group_id"]

    data = {
        "title": payload.get("title", ""),
        "question_text": question_text,
        "lang": lang,
        "target_countries": target_countries,
        "target_genders": target_genders,
        "type": survey_type,
        "status": status,
        "is_active": payload.get("is_active", True),
        "is_single_choice": is_single_choice,
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

    # Remove existing translations
    others = (
        supabase_admin.table("surveys")
        .select("id,lang")
        .eq("group_id", group_id)
        .execute()
        .data
        or []
    )
    for row in others:
        sid = row["id"]
        if sid == survey_id:
            continue
        supabase_admin.table("survey_items").delete().eq("survey_id", sid).execute()
        supabase_admin.table("surveys").delete().eq("id", sid).execute()

    # Determine target languages for translation
    targets = list(BASE_TARGET_LANGS)
    if lang != "ja":
        targets.append("ja")
    if lang in targets:
        targets.remove(lang)

    base_title = data.get("title", "")
    base_items = item_rows

    for tgt in targets:
        try:
            translated_question = translate_with_openai(_build_prompt(question_text, tgt))
            translated_title = (
                translate_with_openai(_build_prompt(base_title, tgt)) if base_title else ""
            )
            translated_options = [
                translate_with_openai(_build_prompt(it["body"], tgt)) for it in base_items
            ]
        except Exception as exc:  # pragma: no cover
            logger.error("Translation %s failed for survey %s: %s", tgt, group_id, exc, exc_info=True)
            continue

        trans_row = {
            "title": translated_title,
            "question_text": translated_question,
            "lang": tgt,
            "target_countries": target_countries,
            "target_genders": target_genders,
            "type": survey_type,
            "status": status,
            "is_active": True,
            "group_id": group_id,
            "is_single_choice": is_single_choice,
        }
        res_t = supabase_admin.table("surveys").insert(trans_row).execute()
        if not (res_t.data):
            continue
        new_tid = res_t.data[0]["id"]
        trans_items = []
        for base_it, body in zip(base_items, translated_options):
            trans_items.append(
                {
                    "survey_id": new_tid,
                    "position": base_it["position"],
                    "body": body,
                    "is_exclusive": base_it.get("is_exclusive", False),
                    "language": tgt,
                    "is_active": True,
                }
            )
        if trans_items:
            supabase_admin.table("survey_items").insert(trans_items).execute()

    return {"id": survey_id, "group_id": group_id}


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
    # Delete all surveys in the same group, including items
    gid_resp = supabase_admin.table("surveys").select("group_id").eq("id", survey_id).execute()
    group_id = gid_resp.data[0]["group_id"] if gid_resp.data else None
    ids: list[str] = []
    if group_id:
        res_ids = (
            supabase_admin.table("surveys").select("id").eq("group_id", group_id).execute()
        )
        ids = [r["id"] for r in (res_ids.data or [])]
    else:
        ids = [survey_id]

    for sid in ids:
        supabase_admin.table("survey_items").delete().eq("survey_id", sid).execute()
        supabase_admin.table("surveys").delete().eq("id", sid).execute()

    return Response(status_code=204)
