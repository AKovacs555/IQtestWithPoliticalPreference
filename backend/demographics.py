"""Demographic collection helpers.

This module stores demographic information on user records. In a real
application this would persist to Supabase with hashed identifiers.
"""
from __future__ import annotations

from datetime import datetime
from . import main


def collect_demographics(
    age_band: str, gender: str, income_band: str, occupation: str, user_id: str
) -> None:
    """Store demographic details for ``user_id``.

    The data are saved on the in-memory user record referenced by the
    hashed ``user_id``. Each update overwrites the previous values and
    records the update timestamp. When deploying with a real database this
    function should perform an UPSERT into the demographics table.
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
        "occupation": occupation,
        "updated": datetime.utcnow().isoformat(),
    }
