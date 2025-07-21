"""Placeholders for upcoming features per design overview."""

from typing import List, Optional
from datetime import datetime

from . import main

from .dp import add_laplace


def dp_average(values: List[float], epsilon: float, min_count: int = 100) -> Optional[float]:
    """Return the differentially private average of ``values``.

    If ``values`` has fewer than ``min_count`` elements the function returns
    ``None`` to avoid revealing small aggregates. Laplace noise scaled by
    ``epsilon`` is applied to the resulting mean.
    """
    if len(values) < min_count:
        return None
    mean = sum(values) / len(values)
    return add_laplace(mean, epsilon, sensitivity=1 / len(values))


def collect_demographics(age_band: str, gender: str, income_band: str, user_id: str) -> None:
    """Store demographic data in-memory.

    In production this should persist to the database with appropriate
    encryption and hashing. Here we simply store the values on the user
    record for demonstration purposes.
    """
    user = main.USERS.setdefault(
        user_id,
        {
            "salt": "",
            "plays": 0,
            "referrals": 0,
            "scores": [],
            "party_log": [],
            "demographics": {},
        },
    )
    user["demographics"] = {
        "age_band": age_band,
        "gender": gender,
        "income_band": income_band,
        "updated": datetime.utcnow().isoformat(),
    }


def update_party_affiliation(user_id: str, party_ids: List[int]) -> None:
    """Record supported parties and log change history."""
    user = main.USERS.setdefault(
        user_id,
        {
            "salt": "",
            "plays": 0,
            "referrals": 0,
            "scores": [],
            "party_log": [],
            "demographics": {},
        },
    )
    user.setdefault("party_log", []).append(
        {"timestamp": datetime.utcnow().isoformat(), "party_ids": party_ids}
    )
    user["party_ids"] = party_ids


def leaderboard_by_party(epsilon: float = 1.0) -> List[dict]:
    """Return average IQ by party with differential privacy."""
    buckets = {}
    for user in main.USERS.values():
        parties = user.get("party_ids")
        scores = [s.get("iq") for s in user.get("scores", [])]
        if not parties or not scores:
            continue
        avg_score = sum(scores) / len(scores)
        for pid in parties:
            buckets.setdefault(pid, []).append(avg_score)

    results = []
    for pid, vals in buckets.items():
        avg = dp_average(vals, epsilon)
        if avg is None:
            continue
        results.append({"party_id": pid, "avg_iq": avg, "n": len(vals)})
    return results


def generate_share_image(user_id: str, iq: float, percentile: float) -> str:
    """Return a URL to a generated result image for social sharing.

    TODO: create an image with OpenGraph/Twitter metadata and upload to storage.
    """
    raise NotImplementedError


def update_normative_distribution(new_scores: List[float]) -> None:
    """Recompute normative distribution with incoming scores."""
    # TODO: load existing distribution, merge with ``new_scores`` and store back
    #       to ``backend/data/normative_distribution.json``
    raise NotImplementedError
