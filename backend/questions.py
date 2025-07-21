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


def available_sets() -> List[str]:
    """Return a list of available question set IDs (filenames without extension)."""
    if not POOL_PATH.exists():
        return []
    return [p.stem for p in POOL_PATH.glob("*.json")]


def load_questions(set_id: str | None = None) -> List[Dict[str, Any]]:
    """Load question files from :data:`POOL_PATH`.

    Parameters
    ----------
    set_id:
        Optional set identifier.  If provided, only the file matching
        ``{set_id}.json`` will be loaded.  Otherwise all files are merged.
    """
    questions: List[Dict[str, Any]] = []
    if not POOL_PATH.exists():
        return questions
    seen_ids = set()
    next_id = 0
    paths = (
        [POOL_PATH / f"{set_id}.json"] if set_id else sorted(POOL_PATH.glob("*.json"))
    )
    for path in paths:
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


def get_random_questions(n: int, set_id: str | None = None) -> List[Dict[str, Any]]:
    """Return ``n`` random non-repeating questions.

    If ``set_id`` is provided, the questions are drawn only from that set.
    Otherwise the global pool is used.
    """

    pool = load_questions(set_id) if set_id else DEFAULT_QUESTIONS
    if n > len(pool):
        raise ValueError("Not enough questions in pool")
    return random.sample(pool, n)

