import os
import json
import uuid
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from backend.routes.admin_questions import check_admin
from backend.deps.supabase_client import get_supabase_client
from backend.utils.translation import translate_question

router = APIRouter(prefix="/admin", tags=["admin-questions"])


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
    records = []
    supabase = get_supabase_client()
    existing = supabase.table("questions").select("id").execute()
    existing_ids = {row["id"] for row in existing.data} if existing.data else set()
    next_id = max(existing_ids) + 1 if existing_ids else 0
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail=f"Item {idx} must be object")
        required = {"id", "question", "options", "answer", "irt"}
        if not required.issubset(item):
            raise HTTPException(status_code=400, detail=f"Missing keys in item {idx}")
        options = item["options"]
        if not isinstance(options, list) or len(options) != 4:
            raise HTTPException(status_code=400, detail=f"Options in item {idx} must be list of 4")
        answer = item["answer"]
        if not isinstance(answer, int) or answer < 0 or answer > 3:
            raise HTTPException(status_code=400, detail=f"Answer in item {idx} must be 0-3")
        irt = item["irt"]
        if not isinstance(irt, dict) or "a" not in irt or "b" not in irt:
            raise HTTPException(status_code=400, detail=f"IRT in item {idx} must contain a and b")
        image_val = item.get("image")
        if image_val is not None and not isinstance(image_val, str):
            raise HTTPException(status_code=400, detail=f"Image in item {idx} must be a string")

        language = item.get("language", "ja")
        incoming_id = item["id"]
        group_id = str(uuid.uuid4())

        if incoming_id in existing_ids:
            new_id = next_id
            next_id += 1
        else:
            new_id = incoming_id
        existing_ids.add(new_id)

        base_record = {
            "id": new_id,
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
        records.append(base_record)

        if language == "ja":
            tasks = [translate_question(item["question"], options, lang) for lang in ["en", "tr", "ru", "zh"]]
            results = await asyncio.gather(*tasks)
            for lang, res in zip(["en", "tr", "ru", "zh"], results):
                q_trans, opts_trans = res
                translated_id = next_id
                next_id += 1
                existing_ids.add(translated_id)
                records.append(
                    {
                        "id": translated_id,
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
                )
    resp = supabase.table("questions").insert(records).execute()
    if resp.error:
        raise HTTPException(status_code=500, detail=resp.error.message)
    return {"inserted": len(records)}


@router.post("/import_questions_with_images", dependencies=[Depends(check_admin)])
async def import_questions_with_images(
    json_file: UploadFile = File(...),
    images: List[UploadFile] = File(default=None)
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

    existing = supabase.table("questions").select("id").execute()
    existing_ids = {row["id"] for row in existing.data} if existing.data else set()
    next_id = max(existing_ids) + 1 if existing_ids else 0

    records = []
    for idx, item in enumerate(data):
        required = {"id", "question", "options", "answer", "irt"}
        if not required.issubset(item):
            raise HTTPException(status_code=400, detail=f"Missing keys in item {idx}")
        if not isinstance(item["options"], list) or len(item["options"]) != 4:
            raise HTTPException(status_code=400, detail=f"Options in item {idx} must be list of 4")

        incoming_id = item["id"]
        group_id = str(uuid.uuid4())
        if incoming_id in existing_ids:
            new_id = next_id
            next_id += 1
        else:
            new_id = incoming_id
        existing_ids.add(new_id)

        image_url = None
        filename = item.get("image_filename") or item.get("image") or item.get("image_prompt")
        if filename and filename in image_map:
            file_obj = image_map[filename]
            supabase.storage.from_("question-images").upload(
                file_obj.filename, await file_obj.read(), {"cacheControl": "3600", "upsert": True}
            )
            image_url = supabase.storage.from_("question-images").get_public_url(file_obj.filename)
        elif isinstance(filename, str) and filename.startswith("http"):
            image_url = filename

        language = item.get("language", "ja")

        base_record = {
            "id": new_id,
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
        records.append(base_record)

        if language == "ja":
            tasks = [translate_question(item["question"], item["options"], lang) for lang in ["en", "tr", "ru", "zh"]]
            results = await asyncio.gather(*tasks)
            for lang, res in zip(["en", "tr", "ru", "zh"], results):
                q_trans, opts_trans = res
                translated_id = next_id
                next_id += 1
                existing_ids.add(translated_id)
                records.append(
                    {
                        "id": translated_id,
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
                )

    resp = supabase.table("questions").insert(records).execute()
    if resp.error:
        raise HTTPException(status_code=500, detail=resp.error.message)
    return {"inserted": len(records)}
