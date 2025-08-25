from fastapi import APIRouter, Depends, Header, Query, HTTPException
from backend.deps.supabase_client import get_supabase_client
from backend.deps.auth import get_current_user as _get_current_user, User
from backend.utils.num import safe_float, to_2f
from backend.services import db_read
from fastapi.responses import JSONResponse
import math

router = APIRouter(tags=["leaderboard"])


async def maybe_user(authorization: str = Header(None)) -> User | None:
    if not authorization:
        return None
    try:
        return await _get_current_user(authorization)
    except HTTPException:
        return None


@router.get("/leaderboard")
async def get_leaderboard(limit: int = Query(100), user: User | None = Depends(maybe_user)):
    supabase = get_supabase_client()
    limit = max(1, min(limit, 10000))
    resp = (
        supabase.table("leaderboard_best")
        .select("user_id,best_iq")
        .order("best_iq", desc=True)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        rows = (
            supabase.table("user_best_iq_unified")
            .select("user_id,best_iq")
            .execute()
            .data
            or []
        )
        rows.sort(key=lambda r: safe_float(r.get("best_iq")) or -math.inf, reverse=True)
    total_users = len(rows)
    top = rows[:limit]

    user_ids = [r.get("user_id") for r in top if r.get("user_id")]
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
    for rank, row in enumerate(top, start=1):
        uid = row.get("user_id")
        iq = safe_float(row.get("best_iq"))
        if uid is None or iq is None or not math.isfinite(iq):
            continue
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
    if user:
        uid = user.get("hashed_id")
        my_rank = next(
            (idx + 1 for idx, r in enumerate(rows) if r.get("user_id") == uid),
            None,
        )

    payload = {"total_users": total_users, "items": items, "my_rank": my_rank}
    return JSONResponse(payload, headers=db_read.cache_headers(payload))
