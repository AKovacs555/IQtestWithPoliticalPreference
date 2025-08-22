from fastapi import APIRouter
from backend import db


def get_supabase():
    return db.get_supabase()

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
    except Exception:
        # Never block login on failure
        pass

    return {"points": db.get_points(user_id)}

