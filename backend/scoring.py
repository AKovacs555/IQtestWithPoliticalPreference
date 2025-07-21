import math
from typing import List

from .irt import prob_correct, percentile

# Two-parameter logistic IRT ability estimation

def estimate_theta(responses: List[dict], iterations: int = 10) -> float:
    """Estimate latent ability theta from question responses.

    Each response dict should contain 'a', 'b' and 'correct' fields.
    """
    theta = 0.0
    for _ in range(iterations):
        num = 0.0
        den = 0.0
        for r in responses:
            p = prob_correct(theta, r['a'], r['b'])
            num += r['a'] * (r['correct'] - p)
            den += (r['a'] ** 2) * p * (1 - p)
        if den == 0:
            break
        theta += num / den
    return theta


def iq_score(theta: float) -> float:
    """Convert theta to a standard IQ scale (mean 100, sd 15)."""
    return 15 * theta + 100


def ability_summary(theta: float) -> str:
    """Return a short ability range description."""
    if theta < -1:
        return "below average"
    if theta < 1:
        return "around average"
    return "above average"


def standard_error(theta: float, responses: List[dict]) -> float | None:
    """Return standard error of theta estimate."""
    info = 0.0
    for r in responses:
        p = prob_correct(theta, r["a"], r["b"])
        info += (r["a"] ** 2) * p * (1 - p)
    return (1 / math.sqrt(info)) if info > 0 else None


