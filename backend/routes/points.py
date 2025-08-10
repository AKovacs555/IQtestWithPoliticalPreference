from fastapi import APIRouter
from backend.deps.supabase_client import get_supabase_client

router = APIRouter(prefix="/points", tags=["points"])


@router.get("/{user_id}")
async def get_points(user_id: str):
    supabase = get_supabase_client()
    user = (
        supabase.table("app_users")
        .select("points")
        .eq("id", user_id)
        .execute()
        .data
    )
    if not user:
        supabase.table("app_users").insert(
            {
                "id": user_id,
                "hashed_id": user_id,
                "points": 0,
                "free_attempts": 1,
            }
        ).execute()
        return {"points": 0}
    return {"points": user[0].get("points", 0)}
