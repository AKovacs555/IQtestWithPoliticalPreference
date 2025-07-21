"""Question bank loader with psychometric metadata.

This module loads question sets from the repository level ``questions``
directory.  Each file is expected to contain an object with the
following structure::

    {
        "id": "set01",
        "language": "en",
        "title": "Sample",
        "questions": [
            {
                "id": 0,
                "text": "...",
                "options": ["A", "B"],
                "correct_index": 1,
                "explanation": "..."
            },
            ...
        ]
    }

IDs must be globally unique across all files.  ``load_questions`` will
assign sequential IDs if duplicates are found so that callers can rely on
stable identifiers.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any
from jsonschema import validate, ValidationError

# Question sets are stored under the repository level ``questions`` directory
# so that new sets can be added without modifying the code base.
POOL_PATH = Path(__file__).resolve().parents[1] / "questions"
SCHEMA_PATH = POOL_PATH / "schema.json"


def available_sets() -> List[str]:
    """Return a list of available question set IDs."""
    if not POOL_PATH.exists():
        return []
    ids = []
    for p in POOL_PATH.glob("*.json"):
        try:
            with p.open() as f:
                data = json.load(f)
            ids.append(data.get("id", p.stem))
        except Exception:
            continue
    return ids


def load_questions(set_id: str | None = None) -> List[Dict[str, Any]]:
    """Load question files from :data:`POOL_PATH`.

    Each file contains an object with a ``questions`` array.  ``text`` and
    ``correct_index`` fields are mapped to ``question`` and ``answer`` for
    backward compatibility.
    """

    questions: List[Dict[str, Any]] = []
    if not POOL_PATH.exists():
        return questions

    # Validate files before loading
    validate_questions(set_id)

    seen_ids = set()
    next_id = 0
    paths = [POOL_PATH / f"{set_id}.json"] if set_id else sorted(POOL_PATH.glob("*.json"))

    for path in paths:
        with path.open() as f:
            data = json.load(f)
        for item in data.get("questions", []):
            qid = item.get("id")
            if qid is None or qid in seen_ids:
                item["id"] = next_id
            else:
                item["id"] = qid
            seen_ids.add(item["id"])
            item["question"] = item.pop("text")
            item["answer"] = item.pop("correct_index")
            questions.append(item)
            next_id = max(next_id, item["id"] + 1)
    return questions


def validate_questions(set_id: str | None = None) -> None:
    """Validate question files against the schema and check ID uniqueness."""
    if not SCHEMA_PATH.exists():
        return

    with SCHEMA_PATH.open() as f:
        schema = json.load(f)

    paths = [POOL_PATH / f"{set_id}.json"] if set_id else sorted(POOL_PATH.glob("*.json"))
    seen_ids = set()
    for path in paths:
        with path.open() as f:
            data = json.load(f)
        try:
            validate(data, schema)
        except ValidationError as e:
            raise ValueError(f"{path.name}: {e.message}")
        for item in data.get("questions", []):
            qid = item.get("id")
            if qid in seen_ids:
                raise ValueError(f"Duplicate question id {qid}")
            seen_ids.add(qid)


DEFAULT_QUESTIONS: List[Dict[str, Any]] = []
try:
    validate_questions()
    DEFAULT_QUESTIONS = load_questions()
except Exception as e:
    print(f"Question validation failed: {e}")

# Convenient lookup table by ID
QUESTION_MAP: Dict[int, Dict[str, Any]] = {q["id"]: q for q in DEFAULT_QUESTIONS}


def get_random_questions(n: int, set_id: str | None = None) -> List[Dict[str, Any]]:
    """Return ``n`` random non-repeating questions.

    If ``set_id`` is provided, the questions are drawn only from that set.
    Otherwise the global pool is used.
    """

    pool = load_questions(set_id) if set_id else DEFAULT_QUESTIONS
    if n > len(pool):
        raise ValueError("Not enough questions in pool")
    return random.sample(pool, n)

