from fastapi import APIRouter
from postgrest.exceptions import APIError

from backend.db import get_supabase, insert_attempt_ledger

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/{user_id}")
async def get_points(user_id: str):
    """Return the legacy ``points`` value for ``user_id``.

    The function ensures a minimal ``app_users`` row exists, granting a single
    free attempt on first creation. Missing ``points`` columns are treated as
    zero rather than failing the request.

    Examples
    --------
    >>> from backend.tests.conftest import DummySupabase
    >>> supa = DummySupabase()
    >>> supa.table("app_users").insert({"id": "u1", "hashed_id": "u1", "points": 5}).execute()
    >>> get_supabase = lambda: supa  # doctest: +SKIP
    >>> await get_points("u1")  # doctest: +SKIP
    {'points': 5}
    >>> await get_points("new")  # doctest: +SKIP
    {'points': 0}
    """

    supabase = get_supabase()

    # Ensure minimal row exists (id + hashed_id only)
    try:
        exists = (
            supabase.table("app_users").select("id").eq("id", user_id).single().execute()
        ).data
        if not exists:
            supabase.table("app_users").upsert({"id": user_id, "hashed_id": user_id}).execute()
            insert_attempt_ledger(user_id, 1, "signup")
    except Exception:
        # Never block login on failure
        pass

    # Return legacy points if the column exists, else 0
    try:
        resp = (
            supabase.table("app_users")
            .select("points")
            .eq("id", user_id)
            .single()
            .execute()
        )
        pts = (resp.data or {}).get("points", 0)
        return {"points": int(pts) if isinstance(pts, (int, float)) else 0}
    except APIError as exc:  # missing column or similar
        code = getattr(exc, "code", "")
        if code in ("42703", "PGRST204"):
            return {"points": 0}
        raise

