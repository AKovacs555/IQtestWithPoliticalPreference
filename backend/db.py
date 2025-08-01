import os
from typing import Any, Dict, Optional, List
from supabase import create_client, Client

_supabase: Client | None = None


def get_supabase() -> Client:
    """Return a cached Supabase client."""
    global _supabase
    if _supabase is None:
        supabase_url = os.environ["SUPABASE_URL"]
        supabase_api_key = os.environ["SUPABASE_API_KEY"]
        _supabase = create_client(supabase_url, supabase_api_key)
    return _supabase


def get_user(hashed_id: str) -> Optional[Dict[str, Any]]:
    """Return the user record for the given hash or ``None`` if missing."""
    supabase = get_supabase()
    resp = (
        supabase.from_("users")
        .select("*")
        .eq("hashed_id", hashed_id)
        .limit(1)
        .execute()
    )
    data = resp.data or []
    return data[0] if data else None


def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    supabase = get_supabase()
    resp = supabase.from_("users").insert(user_data).execute()
    return resp.data[0]


def update_user(hashed_id: str, update_data: Dict[str, Any]) -> None:
    supabase = get_supabase()
    supabase.from_("users").update(update_data).eq("hashed_id", hashed_id).execute()


def get_all_users() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.from_("users").select("*").execute()
    return resp.data or []
