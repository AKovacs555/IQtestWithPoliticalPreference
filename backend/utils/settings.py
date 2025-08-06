from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async def get_setting(key: str, default=None):
    """Fetch a setting value by key from the settings table."""
    result = supabase.table("settings").select("value").eq("key", key).execute()
    if result.data:
        return result.data[0].get("value")  # value should be JSON; extract primitive
    return default
