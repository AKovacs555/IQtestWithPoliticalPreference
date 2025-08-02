import os
import json
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Depends

router = APIRouter(prefix="/admin/surveys", tags=["admin-surveys"])

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "political_survey.json")


def check_admin(x_admin_api_key: Optional[str] = Header(None, alias="X-Admin-Api-Key")):
  expected = os.getenv("ADMIN_API_KEY")
  if not expected or x_admin_api_key != expected:
    raise HTTPException(status_code=401, detail="Unauthorized")


def load_data():
  try:
    with open(DATA_PATH) as f:
      return json.load(f)
  except FileNotFoundError:
    return {"questions": [], "parties": []}


def save_data(data: dict):
  with open(DATA_PATH, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/", dependencies=[Depends(check_admin)])
async def list_questions():
  data = load_data()
  return {"questions": data.get("questions", [])}


@router.post("/", dependencies=[Depends(check_admin)])
async def create_question(payload: dict):
  data = load_data()
  questions = data.get("questions", [])
  new_id = max([q.get("id", -1) for q in questions] + [-1]) + 1
  payload["id"] = new_id
  questions.append(payload)
  data["questions"] = questions
  save_data(data)
  return payload


@router.put("/{item_id}", dependencies=[Depends(check_admin)])
async def update_question(item_id: int, payload: dict):
  data = load_data()
  questions = data.get("questions", [])
  for q in questions:
    if q.get("id") == item_id:
      q.update(payload)
      save_data(data)
      return q
  raise HTTPException(status_code=404, detail="Not found")


@router.delete("/{item_id}", dependencies=[Depends(check_admin)])
async def delete_question(item_id: int):
  data = load_data()
  questions = [q for q in data.get("questions", []) if q.get("id") != item_id]
  data["questions"] = questions
  save_data(data)
  return {"deleted": True}
