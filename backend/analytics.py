import os
import time
from typing import Any, Dict


def log_event(event: Dict[str, Any]) -> None:
    """Persist event to Supabase if configured."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_API_KEY")
    if not (supabase_url and supabase_key):
        return
    try:
        from supabase import create_client
    except Exception:
        return
    try:
        supa = create_client(supabase_url, supabase_key)
        supa.table("events").insert({**event, "ts": int(time.time())}).execute()
    except Exception:
        pass
