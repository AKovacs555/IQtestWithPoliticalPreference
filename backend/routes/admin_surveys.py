import os
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

from utils.translation import LANG_NAME_MAP, translate_survey


router = APIRouter(prefix="/admin/surveys", tags=["admin-surveys"])

# Data file storing survey questions and party info
DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "surveys.json"
)


def check_admin(admin_key: Optional[str] = Header(None, alias="X-Admin-Api-Key")):
    """Validate admin API key from headers."""

    expected_new = os.environ.get("ADMIN_API_KEY")
    expected_old = os.environ.get("ADMIN_TOKEN")
    expected = expected_new or expected_old
    if expected is None:
        logging.error("No ADMIN_API_KEY or ADMIN_TOKEN is set in the environment.")
        raise HTTPException(status_code=500, detail="Server misconfigured: missing admin key")
    if admin_key != expected:
        logging.warning(
            f"Invalid admin key provided: {admin_key[:4]}… (expected length {len(expected)})"
        )
        raise HTTPException(status_code=401, detail="Unauthorized")


def load_data() -> dict:
    """Load survey data from ``DATA_PATH``.

    If the file does not yet exist, create it with an empty
    structure so both the admin endpoints and the user-facing
    survey share the same persistent storage.
    """
    try:
        with open(DATA_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        data = {"questions": [], "parties": []}
        save_data(data)
        return data


def save_data(data: dict) -> None:
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _next_id(questions: list[dict]) -> int:
    return max([q.get("id", -1) for q in questions] + [-1]) + 1


def _next_group_id(questions: list[dict]) -> int:
    return max([q.get("group_id", -1) for q in questions] + [-1]) + 1


@router.get("/", dependencies=[Depends(check_admin)])
async def list_questions(lang: Optional[str] = None):
    """List questions grouped by ``group_id``.

    If ``lang`` is provided the representative question will be the one matching
    that language when available; otherwise the first encountered entry for the
    group is returned.
    """

    data = load_data()
    grouped: dict[int, dict] = {}
    for q in data.get("questions", []):
        gid = q.get("group_id")
        if lang and q.get("lang") == lang:
            grouped[gid] = q
        elif gid not in grouped:
            grouped[gid] = q

    return {"questions": list(grouped.values())}


@router.get("/languages", dependencies=[Depends(check_admin)])
async def get_languages():
    """Return supported language codes."""

    return {"languages": list(LANG_NAME_MAP.keys())}


@router.post("/", dependencies=[Depends(check_admin)])
async def create_question(payload: dict):
    """Create a new survey question with translations."""

    data = load_data()
    questions = data.get("questions", [])

    base_lang = payload.get("lang")
    statement = payload.get("statement")
    options = payload.get("options")
    q_type = payload.get("type", "sa")
    exclusive = payload.get("exclusive_options", [])

    if not base_lang or not statement or not options:
        raise HTTPException(status_code=400, detail="Missing required fields")

    group_id = _next_group_id(questions)

    # Create base entry
    new_entries = []
    next_id = _next_id(questions)
    base_entry = {
        "id": next_id,
        "group_id": group_id,
        "lang": base_lang,
        "statement": statement,
        "options": options,
        "type": q_type,
        "exclusive_options": exclusive,
        "lr": payload.get("lr", 0),
        "auth": payload.get("auth", 0),
    }
    new_entries.append(base_entry)
    next_id += 1

    # Generate translations
    for lang_code in LANG_NAME_MAP.keys():
        if lang_code == base_lang:
            continue
        translated_statement, translated_options = await translate_survey(
            statement, options, lang_code
        )
        new_entries.append(
            {
                "id": next_id,
                "group_id": group_id,
                "lang": lang_code,
                "statement": translated_statement,
                "options": translated_options,
                "type": q_type,
                "exclusive_options": exclusive,
                "lr": payload.get("lr", 0),
                "auth": payload.get("auth", 0),
            }
        )
        next_id += 1

    questions.extend(new_entries)
    data["questions"] = questions
    save_data(data)
    return base_entry


@router.put("/{group_id}", dependencies=[Depends(check_admin)])
async def update_question(group_id: int, payload: dict):
    """Update a survey question and regenerate translations."""

    data = load_data()
    questions = data.get("questions", [])
    base_lang = payload.get("lang")
    statement = payload.get("statement")
    options = payload.get("options")
    q_type = payload.get("type", "sa")
    exclusive = payload.get("exclusive_options", [])

    if not base_lang or not statement or not options:
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Remove existing entries for group_id
    questions = [q for q in questions if q.get("group_id") != group_id]

    next_id = _next_id(questions)
    updated_entries = []
    base_entry = {
        "id": next_id,
        "group_id": group_id,
        "lang": base_lang,
        "statement": statement,
        "options": options,
        "type": q_type,
        "exclusive_options": exclusive,
        "lr": payload.get("lr", 0),
        "auth": payload.get("auth", 0),
    }
    updated_entries.append(base_entry)
    next_id += 1

    for lang_code in LANG_NAME_MAP.keys():
        if lang_code == base_lang:
            continue
        translated_statement, translated_options = await translate_survey(
            statement, options, lang_code
        )
        updated_entries.append(
            {
                "id": next_id,
                "group_id": group_id,
                "lang": lang_code,
                "statement": translated_statement,
                "options": translated_options,
                "type": q_type,
                "exclusive_options": exclusive,
                "lr": payload.get("lr", 0),
                "auth": payload.get("auth", 0),
            }
        )
        next_id += 1

    questions.extend(updated_entries)
    data["questions"] = questions
    save_data(data)
    return base_entry


@router.delete("/{group_id}", dependencies=[Depends(check_admin)])
async def delete_question(group_id: int):
    """Delete all entries that belong to ``group_id``."""

    data = load_data()
    questions = [q for q in data.get("questions", []) if q.get("group_id") != group_id]
    data["questions"] = questions
    save_data(data)
    return {"deleted": True}

