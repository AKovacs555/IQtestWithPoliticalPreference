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
    "validate_questions",
    "get_random_questions",
    "get_balanced_random_questions",
    "DEFAULT_QUESTIONS",
    "QUESTION_MAP",
    "QUESTION_BANK",
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
    n: int, split: Tuple[float, float, float] = (0.3, 0.4, 0.3)
) -> List[Dict[str, Any]]:
    """Return ``n`` questions sampled by difficulty.

    ``split`` defines the fraction of easy, medium and hard items. The
    function tolerates small deviations when the pool does not contain
    enough questions of a given difficulty.
    """

    if not QUESTION_BANK:
        raise ValueError("Question bank is empty")

    groups = {1: [], 2: [], 3: []}
    for q in QUESTION_BANK:
        groups.setdefault(q.get("difficulty", 2), []).append(q)

    counts = [round(n * p) for p in split]
    # ensure total matches n
    counts[2] = n - counts[0] - counts[1]

    selected: List[Dict[str, Any]] = []
    for diff_level, count in zip([1, 2, 3], counts):
        pool = groups.get(diff_level, [])
        take = min(count, len(pool))
        if take:
            selected.extend(random.sample(pool, take))

    # fill any shortfall with remaining items
    if len(selected) < n:
        remaining = [q for q in QUESTION_BANK if q not in selected]
        if len(remaining) < n - len(selected):
            raise ValueError("Not enough questions in bank")
        selected.extend(random.sample(remaining, n - len(selected)))

    return selected

