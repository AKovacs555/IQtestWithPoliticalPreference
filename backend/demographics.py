"""Demographic collection helpers.

This module stores demographic information on user records. In a real
application this would persist to Supabase with hashed identifiers.
"""
from __future__ import annotations

from datetime import datetime
from db import update_user


async def collect_demographics(
    age_band: str, gender: str, income_band: str, occupation: str, user_id: str
) -> None:
    """Store demographic details for ``user_id``.

    The data are saved on the in-memory user record referenced by the
    hashed ``user_id``. Each update overwrites the previous values and
    records the update timestamp. When deploying with a real database this
    function should perform an UPSERT into the demographics table.
    """
    update_user(
        user_id,
        {
            "demographic": {
                "age_band": age_band,
                "gender": gender,
                "income_band": income_band,
                "occupation": occupation,
                "updated": datetime.utcnow().isoformat(),
            },
            "demographic_completed": True,
        },
    )

