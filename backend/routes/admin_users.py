from fastapi import APIRouter, Depends, HTTPException
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
