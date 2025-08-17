import os
from datetime import datetime

from .deps.supabase_client import get_supabase_client
from .db import credit_points


def credit_referral_if_applicable(user_id: str) -> None:
    """Credit the referrer with points if applicable.

    Looks for an uncredited row in the ``referrals`` table where
    ``invitee_user`` matches ``user_id``.  If found, the corresponding
    inviter's points are incremented (up to the limit defined by
    the ``REFERRAL_MAX_CREDITS`` environment variable) and the referral row
    is marked as credited.
    """
    supabase = get_supabase_client()
    if not hasattr(supabase, "table"):
        return
    try:
        resp = (
            supabase.table("referrals")
            .select("inviter_code, credited")
            .eq("invitee_user", user_id)
            .single()
            .execute()
        )
        row = getattr(resp, "data", None)
        if not row or row.get("credited"):
            return
        inviter_code = row.get("inviter_code")
        inviter_resp = (
            supabase.table("app_users")
            .select("id")
            .eq("invite_code", inviter_code)
            .single()
            .execute()
        )
        inviter = getattr(inviter_resp, "data", None)
        if not inviter:
            return
        max_credits = int(os.getenv("REFERRAL_MAX_CREDITS", "0"))
        count_resp = (
            supabase.table("referrals")
            .select("id")
            .eq("inviter_code", inviter_code)
            .eq("credited", True)
            .execute()
        )
        credited_count = len(getattr(count_resp, "data", []) or [])
        if credited_count < max_credits:
            credit_points(str(inviter["id"]), 5, "referral_reward", {})
        supabase.table("referrals").update(
            {"credited": True, "credited_at": datetime.utcnow().isoformat()}
        ).eq("invitee_user", user_id).execute()
    except Exception:
        return
