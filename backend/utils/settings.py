from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
try:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    else:
        supabase = None
except Exception:  # pragma: no cover - fallback when client init fails
    supabase = None

async def get_setting(key: str, default=None):
    """Fetch a setting value by key from the settings table."""
    if supabase is None:
        return default
    try:
        result = supabase.table("settings").select("value").eq("key", key).execute()
        if result.data:
            return result.data[0].get("value")
    except Exception:
        return default
    return default
