from typing import List, Optional, Dict

try:
    from .questions import QUESTION_MAP
    from .scoring import standard_error
except ImportError:  # fallback when not part of package
    from questions import QUESTION_MAP
    from scoring import standard_error


def select_next_question(
    theta: float, answered_ids: List[int], pool: List[Dict]
) -> Optional[Dict]:
    """Return the unused question whose ``b`` value is closest to ``theta``."""

    unused = [q for q in pool if q["id"] not in answered_ids]
    if not unused:
        return None
    return min(unused, key=lambda q: abs(q["irt"]["b"] - theta))


def should_stop(theta: float, answers: List[Dict]) -> bool:
    """Return ``True`` if the adaptive test should end."""

    if len(answers) >= 20:
        return True
    se = standard_error(theta, answers)
    return se is not None and se < 0.35


__all__ = ["select_next_question", "should_stop"]
