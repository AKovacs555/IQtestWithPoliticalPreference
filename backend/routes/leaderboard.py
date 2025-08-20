from fastapi import APIRouter, Depends, Header, Query, HTTPException
from backend.deps.supabase_client import get_supabase_client
from backend.deps.auth import get_current_user as _get_current_user, User
from backend.utils.num import safe_float, to_2f
import math

router = APIRouter(tags=["leaderboard"])


async def maybe_user(authorization: str = Header(None)) -> User | None:
    if not authorization:
        return None
    try:
        return _get_current_user(authorization)
    except HTTPException:
        return None


@router.get("/leaderboard")
async def get_leaderboard(limit: int = Query(100), user: User | None = Depends(maybe_user)):
    supabase = get_supabase_client()
    rows = (
        supabase.table("user_best_iq")
        .select("user_id,best_iq")
        .execute()
        .data
        or []
    )

    best: dict[str, float] = {}
    for row in rows:
        uid = row.get("user_id")
        iq = safe_float(row.get("best_iq"))
        if uid is None or iq is None or not math.isfinite(iq):
            continue
        best[uid] = iq

    ordered = sorted(best.items(), key=lambda x: x[1], reverse=True)
    top = ordered[: max(1, min(limit, 10000))]

    user_ids = [uid for uid, _ in top]
    name_map: dict[str, str | None] = {}
    if user_ids:
        users = (
            supabase.table("app_users")
            .select("hashed_id,username")
            .in_("hashed_id", user_ids)
            .execute()
            .data
            or []
        )
        name_map = {
            u.get("hashed_id"): (u.get("username") or None)
            for u in users
        }

    items = []
    for rank, (uid, iq) in enumerate(top, start=1):
        name = name_map.get(uid) or f"Guest-{uid[:4]}"
        items.append(
            {
                "rank": rank,
                "user_id": uid,
                "display_name": name,
                "best_iq": to_2f(iq),
            }
        )

    my_rank = None
    if user and user.get("hashed_id") in best:
        target = user.get("hashed_id")
        my_rank = next(
            (idx + 1 for idx, (uid, _) in enumerate(ordered) if uid == target),
            None,
        )

    return {"total_users": len(ordered), "items": items, "my_rank": my_rank}
