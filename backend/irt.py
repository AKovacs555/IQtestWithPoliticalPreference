"""Simple IRT utilities."""

from math import exp
from typing import Tuple


def prob_correct(theta: float, a: float, b: float) -> float:
    """Return probability of correct answer under 2PL model."""
    return 1 / (1 + exp(-a * (theta - b)))


def update_theta(
    theta: float, a: float, b: float, correct: bool, lr: float = 0.1
) -> float:
    """Update ability estimate with gradient step."""
    p = prob_correct(theta, a, b)
    error = (1 if correct else 0) - p
    return theta + lr * a * error


def percentile(score: float, distribution: list) -> float:
    count = sum(1 for x in distribution if x <= score)
    return 100 * count / len(distribution)
