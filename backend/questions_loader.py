import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import itertools

# Path to repository root questions directory
QUESTIONS_DIR = Path(__file__).resolve().parents[1] / "questions"

@dataclass
class Question:
    id: str
    type: str
    prompt: str
    image: str | None
    options: List[Dict]
    answer: int
    difficulty: int
    tags: List[str]

_question_sets: Dict[str, List[Question]] = {}


def _load_sets() -> None:
    if not QUESTIONS_DIR.exists():
        return
    for path in QUESTIONS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            questions = [
                Question(
                    id=q.get("id"),
                    type=q.get("type", ""),
                    prompt=q.get("prompt", ""),
                    image=q.get("image"),
                    options=q.get("options", []),
                    answer=q.get("answer"),
                    difficulty=int(q.get("difficulty", 1)),
                    tags=q.get("tags", []),
                )
                for q in data.get("questions", [])
            ]
            _question_sets[path.stem] = questions
        except Exception:
            continue


_load_sets()


def get_question_sets() -> List[str]:
    """Return available question set names."""
    return sorted(_question_sets.keys())


def _balance_by_tags(pool: List[Question], k: int) -> List[Question]:
    if k <= 0 or not pool:
        return []
    tags = sorted({t for q in pool for t in q.tags})
    tag_cycle = itertools.cycle(tags) if tags else itertools.cycle([None])
    selected: List[Question] = []
    remaining = pool.copy()
    while len(selected) < k and remaining:
        tag = next(tag_cycle)
        candidates = [q for q in remaining if tag is None or tag in q.tags]
        if not candidates:
            candidates = remaining
        choice = random.choice(candidates)
        selected.append(choice)
        remaining.remove(choice)
    return selected


def get_questions_for_set(set_name: str, num_questions: int, lang: str | None = None) -> List[Dict]:
    """Return a balanced random sample from ``set_name``.

    Difficulty is balanced roughly 30/40/30 across levels 1,2,3+ and
    tags are rotated for diversity.
    """
    if set_name not in _question_sets:
        raise ValueError("unknown_set")
    pool = _question_sets[set_name]
    if len(pool) < num_questions:
        raise ValueError("insufficient_questions")
    easy = [q for q in pool if q.difficulty <= 1]
    med = [q for q in pool if q.difficulty == 2]
    hard = [q for q in pool if q.difficulty >= 3]
    k_easy = int(round(num_questions * 0.3))
    k_med = int(round(num_questions * 0.4))
    k_hard = num_questions - k_easy - k_med

    selected: List[Question] = []
    for group, k in ((easy, k_easy), (med, k_med), (hard, k_hard)):
        selected.extend(_balance_by_tags(group, min(k, len(group))))
    if len(selected) < num_questions:
        remaining = [q for q in pool if q not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[: num_questions - len(selected)])
    random.shuffle(selected)
    return [q.__dict__ for q in selected]

