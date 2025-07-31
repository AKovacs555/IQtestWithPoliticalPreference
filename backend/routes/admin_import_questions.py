import os
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from backend.routes.admin_questions import check_admin
from backend.deps.supabase_client import get_supabase_client

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
        incoming_id = item["id"]
        if incoming_id in existing_ids:
            new_id = next_id
            next_id += 1
        else:
            new_id = incoming_id
        existing_ids.add(new_id)
        records.append({
            "id": new_id,
            "orig_id": incoming_id,
            "question": item["question"],
            "options": options,
            "answer": answer,
            "irt_a": irt["a"],
            "irt_b": irt["b"],
            "image_prompt": item.get("image_prompt"),
        })
    resp = supabase.table("questions").insert(records).execute()
    if resp.error:
        raise HTTPException(status_code=500, detail=resp.error.message)
    return {"inserted": len(records)}
