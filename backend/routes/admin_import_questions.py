import json
import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.routes.admin_questions import check_admin
from backend.deps.supabase_client import get_supabase_client
from backend.utils.translation import translate_question

# Supported languages for automatic translation, including Turkish and Italian
target_languages = ["en", "tr", "ru", "zh", "ko", "es", "fr", "it", "de", "ar"]

router = APIRouter(prefix="/admin", tags=["admin-questions"])

logger = logging.getLogger(__name__)


@router.post("/import_questions", dependencies=[Depends(check_admin)])
async def import_questions(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="File required")
    contents = await file.read()
    try:
        data = json.loads(contents)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON must be an array")

    supabase = get_supabase_client()
    inserted = 0
    for idx, item in enumerate(data):
        group_id = str(uuid.uuid4())
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail=f"Item {idx} must be object")
        required = {"id", "question", "options", "answer", "irt"}
        if not required.issubset(item):
            raise HTTPException(status_code=400, detail=f"Missing keys in item {idx}")
        options = item["options"]
        if not isinstance(options, list) or len(options) != 4:
            raise HTTPException(
                status_code=400, detail=f"Options in item {idx} must be list of 4"
            )
        answer = item["answer"]
        if not isinstance(answer, int) or answer < 0 or answer > 3:
            raise HTTPException(
                status_code=400, detail=f"Answer in item {idx} must be 0-3"
            )
        irt = item["irt"]
        if not isinstance(irt, dict) or "a" not in irt or "b" not in irt:
            raise HTTPException(
                status_code=400, detail=f"IRT in item {idx} must contain a and b"
            )
        image_val = item.get("image")
        if image_val is not None and not isinstance(image_val, str):
            raise HTTPException(
                status_code=400, detail=f"Image in item {idx} must be a string"
            )

        language = item.get("language", "ja")
        incoming_id = item["id"]
        if not isinstance(incoming_id, (int, str)):
            incoming_id = str(incoming_id)

        record = {
            "orig_id": incoming_id,
            "group_id": group_id,
            "question": item["question"],
            "options": options,
            "answer": answer,
            "irt_a": irt["a"],
            "irt_b": irt["b"],
            "language": language,
            "image_prompt": item.get("image_prompt"),
            "image": image_val,
        }
        try:
            supabase.table("questions").insert(record).execute()
            inserted += 1
        except Exception as exc:
            logger.error(
                f"Failed to insert record (lang={record['language']}, orig_id={record['orig_id']}): {exc}"
            )
            continue

        if language == "ja":
            for lang in target_languages:
                try:
                    q_trans, opts_trans = await translate_question(
                        item["question"], options, lang
                    )
                except Exception as exc:
                    logger.error(
                        f"Translation {lang} failed for orig_id {incoming_id}: {exc}"
                    )
                    continue
                trans_record = {
                    "orig_id": incoming_id,
                    "group_id": group_id,
                    "question": q_trans,
                    "options": opts_trans,
                    "answer": answer,
                    "irt_a": irt["a"],
                    "irt_b": irt["b"],
                    "language": lang,
                    "image_prompt": item.get("image_prompt"),
                    "image": image_val,
                }
                try:
                    supabase.table("questions").insert(trans_record).execute()
                    inserted += 1
                except Exception as exc:
                    logger.error(
                        f"Failed to insert record (lang={trans_record['language']}, orig_id={trans_record['orig_id']}): {exc}"
                    )
                    continue
    return {"inserted": inserted}


@router.post("/import_questions_with_images", dependencies=[Depends(check_admin)])
async def import_questions_with_images(
    json_file: UploadFile = File(...), images: List[UploadFile] = File(default=None)
):
    """Import questions from a JSON file and upload images to Supabase Storage."""
    contents = await json_file.read()
    try:
        data = json.loads(contents)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="JSON must be an array")

    image_map = {}
    if images:
        for img in images:
            image_map[img.filename] = img

    supabase = get_supabase_client()

    inserted = 0
    for idx, item in enumerate(data):
        group_id = str(uuid.uuid4())
        required = {"id", "question", "options", "answer", "irt"}
        if not required.issubset(item):
            raise HTTPException(status_code=400, detail=f"Missing keys in item {idx}")
        if not isinstance(item["options"], list) or len(item["options"]) != 4:
            raise HTTPException(
                status_code=400, detail=f"Options in item {idx} must be list of 4"
            )

        incoming_id = item["id"]
        if not isinstance(incoming_id, (int, str)):
            incoming_id = str(incoming_id)

        image_url = None
        filename = (
            item.get("image_filename") or item.get("image") or item.get("image_prompt")
        )
        if filename and filename in image_map:
            file_obj = image_map[filename]
            supabase.storage.from_("question-images").upload(
                file_obj.filename,
                await file_obj.read(),
                {"cacheControl": "3600", "upsert": True},
            )
            image_url = supabase.storage.from_("question-images").get_public_url(
                file_obj.filename
            )
        elif isinstance(filename, str) and filename.startswith("http"):
            image_url = filename

        language = item.get("language", "ja")

        record = {
            "orig_id": incoming_id,
            "group_id": group_id,
            "question": item["question"],
            "options": item["options"],
            "answer": item["answer"],
            "irt_a": item["irt"]["a"],
            "irt_b": item["irt"]["b"],
            "language": language,
            "image_prompt": item.get("image_prompt"),
            "image": image_url,
        }
        try:
            supabase.table("questions").insert(record).execute()
            inserted += 1
        except Exception as exc:
            logger.error(
                f"Failed to insert record (lang={record['language']}, orig_id={record['orig_id']}): {exc}"
            )
        else:
            if language == "ja":
                for lang in target_languages:
                    try:
                        q_trans, opts_trans = await translate_question(
                            item["question"], item["options"], lang
                        )
                    except Exception as exc:
                        logger.error(
                            f"Translation {lang} failed for orig_id {incoming_id}: {exc}"
                        )
                        continue
                    trans_record = {
                        "orig_id": incoming_id,
                        "group_id": group_id,
                        "question": q_trans,
                        "options": opts_trans,
                        "answer": item["answer"],
                        "irt_a": item["irt"]["a"],
                        "irt_b": item["irt"]["b"],
                        "language": lang,
                        "image_prompt": item.get("image_prompt"),
                        "image": image_url,
                    }
                    try:
                        supabase.table("questions").insert(trans_record).execute()
                        inserted += 1
                    except Exception as exc:
                        logger.error(
                            f"Failed to insert record (lang={trans_record['language']}, orig_id={trans_record['orig_id']}): {exc}"
                        )
                        continue
    return {"inserted": inserted}
