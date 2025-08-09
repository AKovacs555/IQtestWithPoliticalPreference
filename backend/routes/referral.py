import random
from fastapi import APIRouter, HTTPException, Depends

from backend.deps.supabase_client import get_supabase_client
from backend.deps.auth import get_current_user

router = APIRouter(prefix="/referral", tags=["referral"])


def _generate_code() -> str:
    return "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))


@router.get("/code")
async def get_invite_code(user: dict = Depends(get_current_user)):
    """Return the user's invite code, generating one if missing."""
    supabase = get_supabase_client()
    code = user.get("invite_code")
    if not code:
        code = _generate_code()
        supabase.table("app_users").update({"invite_code": code}).eq(
            "hashed_id", user["hashed_id"]
        ).execute()
    return {"invite_code": code}


@router.get("/claim")
async def claim_referral(r: str, user: dict = Depends(get_current_user)):
    """Register ``user`` as referred by invite code ``r``.

    A record is inserted into the ``referrals`` table linking the inviter's
    code with the invitee's hashed id. Duplicate claims are ignored.
    """
    supabase = get_supabase_client()
    if not r:
        raise HTTPException(status_code=400, detail="invalid_code")
    if supabase.table("referrals").select("id").eq("invitee_user", user["hashed_id"]).execute().data:
        return {"status": "exists"}
    inviter = (
        supabase.table("app_users")
        .select("hashed_id")
        .eq("invite_code", r)
        .single()
        .execute()
        .data
    )
    if not inviter or inviter["hashed_id"] == user["hashed_id"]:
        raise HTTPException(status_code=400, detail="invalid_code")
    supabase.table("referrals").insert(
        {"inviter_code": r, "invitee_user": user["hashed_id"], "credited": False}
    ).execute()
    supabase.table("app_users").update({"referred_by": inviter["hashed_id"]}).eq(
        "hashed_id", user["hashed_id"]
    ).execute()
    return {"status": "ok"}
