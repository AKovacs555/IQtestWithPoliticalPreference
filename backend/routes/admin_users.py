from fastapi import APIRouter, Depends, HTTPException
from urllib.parse import quote

from db import get_supabase, get_points, insert_point_ledger
from .dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin-users"])


@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users():
    """Return a list of all users with their hashed_id and points."""
    supabase = get_supabase()
    rows = supabase.from_("app_users").select("hashed_id, points").execute().data
    return {"users": rows or []}


@router.post("/user/points", dependencies=[Depends(require_admin)])
async def update_points(payload: dict):
    """Update the points value for a given user."""
    user_id = payload.get("user_id")
    points = payload.get("points")
    if user_id is None or points is None:
        raise HTTPException(status_code=400, detail="Missing parameters")
    current = get_points(user_id)
    delta = int(points) - current
    if delta:
        insert_point_ledger(user_id, delta, "admin")
    return {"status": "ok"}


@router.get("/users/search", dependencies=[Depends(require_admin)])
async def search_users(query: str = "", limit: int = 20, offset: int = 0):
    """Search users by email, display name or hashed_id."""

    if not query:
        return {"users": []}
    supabase = get_supabase()
    encoded = quote(query, safe="")
    like = f"*{encoded}*"
    try:
        resp = (
            supabase.table("app_users")
            .select("hashed_id, display_name, email, points")
            .or_(
                f"email.ilike.{like},display_name.ilike.{like},hashed_id.ilike.{like}"
            )
            .limit(limit)
            .offset(offset)
            .execute()
        )
        rows = resp.data or []
    except Exception:
        rows = []
    return {"users": rows}


@router.post("/users/{hashed_id}/points/add", dependencies=[Depends(require_admin)])
async def add_points(hashed_id: str, payload: dict):
    """Add or subtract points from a user."""

    delta = payload.get("delta")
    reason = payload.get("reason", "manual")
    if not isinstance(delta, int) or delta == 0:
        raise HTTPException(status_code=400, detail="delta must be non-zero integer")
    current = get_points(hashed_id)
    if delta < 0 and current + delta < 0:
        raise HTTPException(status_code=400, detail="insufficient_points")
    insert_point_ledger(hashed_id, delta, reason)
    return {"points": get_points(hashed_id)}
