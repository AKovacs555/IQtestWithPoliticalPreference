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
from typing import List, Dict, Any, Tuple
from jsonschema import validate, ValidationError

# Question sets are stored under the repository level ``questions`` directory
# so that new sets can be added without modifying the code base.
POOL_PATH = Path(__file__).resolve().parents[1] / "questions"
SCHEMA_PATH = POOL_PATH / "schema.json"
BANK_PATH = Path(__file__).resolve().parent / "data" / "question_bank.json"


def available_sets() -> List[str]:
    """Return a list of available question set IDs."""
    if not POOL_PATH.exists():
        return []
    ids = []
    for p in POOL_PATH.glob("*.json"):
        if p.name == "schema.json":
            continue
        try:
            with p.open() as f:
                data = json.load(f)
            ids.append(data.get("id", p.stem))
        except Exception:
            continue
    return ids


def load_questions(set_id: str | None = None) -> List[Dict[str, Any]]:
    """Load question files from :data:`POOL_PATH`.

    Each file contains an object with a ``questions`` array following
    :mod:`questions/schema.json`. Items must include ``question`` and ``answer``
    fields. Older ``text``/``correct_index`` keys are no longer supported.
    """

    questions: List[Dict[str, Any]] = []
    if not POOL_PATH.exists():
        return questions

    # Validate files before loading
    validate_questions(set_id)

    seen_ids = set()
    next_id = 0
    paths = [POOL_PATH / f"{set_id}.json"] if set_id else sorted(p for p in POOL_PATH.glob("*.json") if p.name != "schema.json")

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
            questions.append(item)
            next_id = max(next_id, item["id"] + 1)
    return questions


def validate_questions(set_id: str | None = None) -> None:
    """Validate question files against ``schema.json``."""
    if not SCHEMA_PATH.exists():
        return
    with SCHEMA_PATH.open() as f:
        schema = json.load(f)
    paths = [POOL_PATH / f"{set_id}.json"] if set_id else sorted(p for p in POOL_PATH.glob("*.json") if p.name != "schema.json")
    for path in paths:
        with path.open() as f:
            data = json.load(f)
        try:
            validate(data, schema)
        except ValidationError as e:
            raise ValueError(f"{path.name} invalid: {e.message}")


DEFAULT_QUESTIONS: List[Dict[str, Any]] = []
try:
    validate_questions()
    DEFAULT_QUESTIONS = load_questions()
except Exception as e:
    print(f"Question validation failed: {e}")

# Load full question bank for balanced sampling
def _load_bank() -> List[Dict[str, Any]]:
    if not BANK_PATH.exists():
        return []
    with BANK_PATH.open() as f:
        return json.load(f)

QUESTION_BANK: List[Dict[str, Any]] = _load_bank()

# Convenient lookup table by ID
QUESTION_MAP: Dict[int, Dict[str, Any]] = {q["id"]: q for q in DEFAULT_QUESTIONS}
QUESTION_MAP.update({q["id"]: q for q in QUESTION_BANK})

__all__ = [
    "available_sets",
    "load_questions",
    "QUESTION_MAP",
    "get_balanced_random_questions",
    "get_balanced_random_questions_by_set",
]


def get_random_questions(n: int, set_id: str | None = None) -> List[Dict[str, Any]]:
    """Return ``n`` random non-repeating questions.

    If ``set_id`` is provided, the questions are drawn only from that set.
    Otherwise the global pool is used.
    """

    pool = load_questions(set_id) if set_id else DEFAULT_QUESTIONS
    if n > len(pool):
        raise ValueError("Not enough questions in pool")
    return random.sample(pool, n)


def get_balanced_random_questions(
    n: int = 20, split: Tuple[float, float, float] = (0.3, 0.4, 0.3)
) -> List[Dict[str, Any]]:
    """Return ``n`` items sampled by difficulty using IRT ``b`` values."""

    easy = [q for q in QUESTION_MAP.values() if q["irt"]["b"] <= -0.33]
    mid = [q for q in QUESTION_MAP.values() if -0.33 < q["irt"]["b"] < 0.33]
    hard = [q for q in QUESTION_MAP.values() if q["irt"]["b"] >= 0.33]

    k_e, k_m, k_h = map(lambda r: int(round(n * r)), split)

    def _pick(group, k):
        if len(group) >= k:
            return random.sample(group, k)
        return list(group)

    selected = _pick(easy, k_e) + _pick(mid, k_m) + _pick(hard, k_h)
    used_ids = {q["id"] for q in selected}
    if len(selected) < n:
        remaining_pool = [q for q in QUESTION_MAP.values() if q["id"] not in used_ids]
        selected += random.sample(remaining_pool, n - len(selected))
    random.shuffle(selected)
    return selected


def get_balanced_random_questions_by_set(
    n: int,
    set_id: str,
    split: Tuple[float, float, float] = (0.3, 0.4, 0.3),
) -> List[Dict[str, Any]]:
    """Sample ``n`` questions from a specific set by difficulty (IRT b values)."""

    pool = load_questions(set_id)
    if n > len(pool):
        raise ValueError("Not enough questions in pool")
    easy = [q for q in pool if q["irt"]["b"] <= -0.33]
    mid = [q for q in pool if -0.33 < q["irt"]["b"] < 0.33]
    hard = [q for q in pool if q["irt"]["b"] >= 0.33]

    k_e, k_m, k_h = map(lambda r: int(round(n * r)), split)

    def _pick(group, k):
        return random.sample(group, k) if len(group) >= k else list(group)

    selected = _pick(easy, k_e) + _pick(mid, k_m) + _pick(hard, k_h)
    used_ids = {q["id"] for q in selected}
    if len(selected) < n:
        remaining_pool = [q for q in pool if q["id"] not in used_ids]
        selected += random.sample(remaining_pool, n - len(selected))
    random.shuffle(selected)
    return selected

