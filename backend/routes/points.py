from fastapi import APIRouter
from backend.deps.supabase_client import get_supabase_client

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/{user_id}")
async def get_points(user_id: str):
    supabase = get_supabase_client()
    from postgrest.exceptions import APIError

    try:
        # Try to fetch the points for this user. `single()` will raise if no row exists.
        resp = (
            supabase.table("app_users")
            .select("points")
            .eq("id", user_id)
            .single()
            .execute()
        )
        data = resp.data or {}
        points = data.get("points", 0)
        return {"points": points if isinstance(points, (int, float)) else 0}
    except APIError:
        # User does not exist or the column is missing: upsert a default record.
        supabase.table("app_users").upsert(
            {
                "id": user_id,
                "hashed_id": user_id,
                "points": 0,
                "free_attempts": 1,
            }
        ).execute()
        return {"points": 0}
