from supabase import Client
from backend.db import get_supabase


def get_supabase_client() -> Client:
    """Dependency to obtain the shared Supabase client."""

    return get_supabase()
