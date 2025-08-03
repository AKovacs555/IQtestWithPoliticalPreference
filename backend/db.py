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


# ---------------------------------------------------------------------------
# Question helpers
# ---------------------------------------------------------------------------


def get_questions(lang: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = (
        supabase.from_("questions").select("*").eq("lang", lang).execute()
    )
    return resp.data or []


def insert_questions(rows: List[Dict[str, Any]]) -> None:
    supabase = get_supabase()
    supabase.from_("questions").insert(rows).execute()


def update_question(question_id: str, data: Dict[str, Any]) -> None:
    supabase = get_supabase()
    supabase.from_("questions").update(data).eq("id", question_id).execute()


def delete_question(question_id: str) -> None:
    supabase = get_supabase()
    supabase.from_("questions").delete().eq("id", question_id).execute()


# ---------------------------------------------------------------------------
# Survey helpers
# ---------------------------------------------------------------------------


def get_surveys(lang: Optional[str] = None) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    query = supabase.from_("surveys").select("*")
    if lang:
        query = query.eq("lang", lang)
    resp = query.execute()
    return resp.data or []


def insert_surveys(rows: List[Dict[str, Any]]) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").insert(rows).execute()


def update_survey(group_id: str, lang: str, data: Dict[str, Any]) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").update(data).eq("group_id", group_id).eq("lang", lang).execute()


def delete_survey(group_id: str) -> None:
    supabase = get_supabase()
    supabase.from_("surveys").delete().eq("group_id", group_id).execute()


def get_parties() -> List[Dict[str, Any]]:
    supabase = get_supabase()
    resp = supabase.from_("parties").select("*").execute()
    return resp.data or []


def insert_parties(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    supabase = get_supabase()
    supabase.from_("parties").insert(rows).execute()
