"""Skeleton Computerized Adaptive Testing (CAT) engine utilities."""
from __future__ import annotations

from math import exp
from typing import Iterable, Optional
import random


def icc_3pl(theta: float, a: float, b: float, c: float = 0.25) -> float:
    """Item characteristic curve for 3PL model."""
    return c + (1 - c) / (1 + exp(-1.7 * a * (theta - b)))


def info_3pl(theta: float, a: float, b: float, c: float = 0.25) -> float:
    """Fisher information for 3PL model."""
    p = icc_3pl(theta, a, b, c)
    q = 1 - p
    if p in (0, 1):
        return 0.0
    return (a ** 2) * ((p - c) ** 2 / ((1 - c) ** 2)) * (q / p)


def update_theta_mle(responses: Iterable[dict], theta: float = 0.0, *, tol: float = 1e-3, max_iter: int = 20) -> float:
    """Very simple Newton-Raphson MLE update."""
    for _ in range(max_iter):
        info = 0.0
        score = 0.0
        for r in responses:
            a = r.get("a", 1.0)
            b = r.get("b", 0.0)
            c = r.get("c", 0.25)
            p = icc_3pl(theta, a, b, c)
            info += info_3pl(theta, a, b, c)
            score += a * (r.get("correct", False) - p)
        if info == 0:
            break
        delta = score / info
        theta += delta
        if abs(delta) < tol:
            break
    return theta


def update_theta_eap(responses: Iterable[dict], theta: float = 0.0) -> float:
    """Placeholder Expected A Posteriori update (currently falls back to MLE)."""
    return update_theta_mle(responses, theta)


def select_next_item(theta: float, pool: Iterable[dict], asked: set[int], *, top_k: int = 5, p_expose: float = 0.6) -> Optional[dict]:
    """Select the next question maximizing information (randomesque)."""
    remaining = [q for q in pool if q.get("id") not in asked]
    scored = sorted(remaining, key=lambda q: info_3pl(theta, q.get("a", 1.0), q.get("b", 0.0)), reverse=True)
    if not scored:
        return None
    k = min(top_k, len(scored))
    top = scored[:k]
    if random.random() < p_expose:
        return top[0]
    return random.choice(top)
