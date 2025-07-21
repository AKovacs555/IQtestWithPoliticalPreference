"""Placeholders for upcoming features per design overview."""

from typing import List, Optional
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




def leaderboard_by_party(epsilon: float = 1.0) -> List[dict]:
    """Return average IQ by party with differential privacy.

    Parties with fewer than ``min_count`` submissions are omitted to
    preserve privacy. Laplace noise is added using :func:`dp_average`.
    """
    buckets: dict[int, List[float]] = {}
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
        avg = dp_average(vals, epsilon, min_count=100)
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
