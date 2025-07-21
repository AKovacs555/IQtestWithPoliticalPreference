"""Question bank loader with psychometric metadata.

This module now supports loading multiple question sets stored under
``backend/data/iq_pool/``.  Each file in that directory is expected to
contain a JSON array of questions with the following schema::

    {
        "id": int,
        "question": str,
        "options": [str, ...],
        "answer": int,
        "difficulty": int,
        "domain": str,
        "irt": {"a": float, "b": float}
    }

IDs must be globally unique across all files.  ``load_questions`` will
assign sequential IDs if duplicates are found so that callers can rely on
stable identifiers.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any

POOL_PATH = Path(__file__).parent / "data" / "iq_pool"


def load_questions() -> List[Dict[str, Any]]:
    """Load all question files from :data:`POOL_PATH`."""
    questions: List[Dict[str, Any]] = []
    if not POOL_PATH.exists():
        return questions
    seen_ids = set()
    next_id = 0
    for path in sorted(POOL_PATH.glob("*.json")):
        with path.open() as f:
            data = json.load(f)
        for item in data:
            qid = item.get("id")
            if qid is None or qid in seen_ids:
                # assign a new sequential id to guarantee global uniqueness
                item["id"] = next_id
            else:
                item["id"] = qid
            seen_ids.add(item["id"])
            questions.append(item)
            next_id = max(next_id, item["id"] + 1)
    return questions


DEFAULT_QUESTIONS: List[Dict[str, Any]] = load_questions()

# Convenient lookup table by ID
QUESTION_MAP: Dict[int, Dict[str, Any]] = {q["id"]: q for q in DEFAULT_QUESTIONS}


def get_random_questions(n: int) -> List[Dict[str, Any]]:
    """Return ``n`` random non-repeating questions."""

    if n > len(DEFAULT_QUESTIONS):
        raise ValueError("Not enough questions in pool")
    return random.sample(DEFAULT_QUESTIONS, n)

