"""Placeholders for upcoming features per design overview."""

from typing import List, Optional

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
    """Store demographic data securely associated with the user.

    TODO: implement persistence in database with encryption/hashing as needed.
    """
    raise NotImplementedError


def update_party_affiliation(user_id: str, party_ids: List[int]) -> None:
    """Allow user to update selected political party once per month.

    Should record history of previous selections.
    """
    raise NotImplementedError


def leaderboard_by_party(epsilon: float = 1.0) -> List[dict]:
    """Return average IQ by party applying differential privacy.

    Only include buckets with at least 100 users. Laplace noise parameter
    `epsilon` should be configurable.
    """
    raise NotImplementedError


def generate_share_image(user_id: str, iq: float, percentile: float) -> str:
    """Return a URL to a generated result image for social sharing.

    TODO: create an image with OpenGraph/Twitter metadata and upload to storage.
    """
    raise NotImplementedError
