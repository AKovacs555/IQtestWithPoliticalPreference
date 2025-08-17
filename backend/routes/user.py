from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel

from backend.deps.supabase_client import get_supabase_client
from backend.db import update_user, get_points
from backend.routes.dependencies import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


class ProfilePayload(BaseModel):
    username: str | None = None


@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    return {
        "id": str(user["id"]) if isinstance(user, dict) else str(user.id),
        "email": user.get("email") if isinstance(user, dict) else getattr(user, "email", None),
        "username": user.get("username") if isinstance(user, dict) else getattr(user, "username", None),
        "is_admin": bool(
            user.get("is_admin") if isinstance(user, dict) else getattr(user, "is_admin", False)
        ),
    }


@router.post("/profile")
async def update_profile(payload: ProfilePayload, user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    data = {}
    if payload.username is not None:
        resp = (
            supabase.table("app_users")
            .select("id")
            .eq("username", payload.username)
            .neq("hashed_id", user.get("hashed_id"))
            .execute()
        )
        if resp.data:
            raise HTTPException(status_code=400, detail="Username already taken")
        data["username"] = payload.username
    if data:
        update_user(supabase, user.get("hashed_id"), data)
        return {"status": "ok", **data}
    return {"status": "ok"}

class NationalityPayload(BaseModel):
    user_id: str
    nationality: str


@router.post("/nationality", status_code=204)
async def set_nationality(payload: NationalityPayload):
    supabase = get_supabase_client()
    update_user(supabase, payload.user_id, {"nationality": payload.nationality})
    return Response(status_code=204)


@router.get("/credits")
async def get_credits(user: dict = Depends(get_current_user)):
    """Return the user's current points balance."""

    points = get_points(str(user.get("id")))
    return {"points": points}


@router.get("/history")
async def get_history(
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user),
):
    supabase = get_supabase_client()
    rows = (
        supabase.table("quiz_attempts")
        .select("*")
        .eq("user_id", user.get("hashed_id"))
        .execute()
        .data
        or []
    )
    rows = [
        r
        for r in rows
        if r.get("status") in {"submitted", "timeout", "abandoned"}
    ]
    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    start = (page - 1) * page_size
    end = start + page_size
    sliced = rows[start:end]
    attempts = [
        {
            "date": r.get("created_at"),
            "set": r.get("set_id"),
            "score": r.get("iq_score"),
            "percentile": r.get("percentile"),
            "duration": r.get("duration"),
        }
        for r in sliced
    ]
    return {"attempts": attempts}

