"""Party affiliation utilities."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from db import AsyncSessionLocal, User

ONE_MONTH = timedelta(days=30)


async def update_party_affiliation(user_id: str, party_ids: List[int]) -> None:
    """Update a user's supported parties.

    Users may change their party selection at most once per month. Each
    update is appended to ``party_log`` with a timestamp. If the latest
    change was less than ``ONE_MONTH`` ago a ``ValueError`` is raised.
    """
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            user = User(hashed_id=user_id, salt="", plays=0, referrals=0, points=0)
            session.add(user)
        log = user.party_log or []
        if log:
            last = datetime.fromisoformat(log[-1]["timestamp"])
            if datetime.utcnow() - last < ONE_MONTH:
                raise ValueError("Party can only be changed once per month")
        if 12 in party_ids and len(party_ids) > 1:
            raise ValueError("無党派 cannot be selected with other parties")
        log.append({"timestamp": datetime.utcnow().isoformat(), "party_ids": party_ids})
        user.party_log = log
        user.party_ids = party_ids
        await session.commit()
