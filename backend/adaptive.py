from typing import List, Optional, Dict

try:
    from .questions import QUESTION_MAP
    from .scoring import standard_error
except ImportError:  # fallback when not part of package
    from questions import QUESTION_MAP
    from scoring import standard_error


def select_next_question(theta: float, asked: List[int], pool: List[int]) -> Optional[Dict]:
    """Return the unused question whose ``b`` value is closest to ``theta``."""
    remaining = [QUESTION_MAP[qid] for qid in pool if qid not in asked]
    if not remaining:
        return None
    return min(remaining, key=lambda q: abs(q["irt"]["b"] - theta))


def should_stop(theta: float, answers: List[Dict]) -> bool:
    """Return ``True`` if the adaptive test should end."""
    if len(answers) >= 20:
        return True
    se = standard_error(
        theta,
        [
            {
                "a": QUESTION_MAP[a["id"]]["irt"]["a"],
                "b": QUESTION_MAP[a["id"]]["irt"]["b"],
                "correct": a["correct"],
            }
            for a in answers
        ],
    )
    return se is not None and se < 0.35


__all__ = ["select_next_question", "should_stop"]
