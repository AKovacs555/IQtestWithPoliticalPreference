"""Party affiliation utilities."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from db import get_user, create_user, update_user, get_supabase

ONE_MONTH = timedelta(days=30)


async def update_party_affiliation(user_id: str, party_ids: List[int]) -> None:
    """Update a user's supported parties.

    Users may change their party selection at most once per month. Each
    update is appended to ``party_log`` with a timestamp. If the latest
    change was less than ``ONE_MONTH`` ago a ``ValueError`` is raised.
    """
    user = get_user(user_id)
    if not user:
        user = create_user(
            {
                "hashed_id": user_id,
            }
        )
    log = user.get("party_log") or []
    if log:
        last = datetime.fromisoformat(log[-1]["timestamp"])
        if datetime.utcnow() - last < ONE_MONTH:
            raise ValueError("Party can only be changed once per month")
    if 12 in party_ids and len(party_ids) > 1:
        raise ValueError("無党派 cannot be selected with other parties")
    log.append({"timestamp": datetime.utcnow().isoformat(), "party_ids": party_ids})
    supabase = get_supabase()
    update_user(supabase, user_id, {"party_log": log})
