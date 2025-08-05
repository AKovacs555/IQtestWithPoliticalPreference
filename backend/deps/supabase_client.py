import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_API_KEY")
    missing = [
        name
        for name, val in [
            ("SUPABASE_URL", url),
            ("SUPABASE_SERVICE_ROLE_KEY or SUPABASE_API_KEY", key),
        ]
        if not val
    ]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return create_client(url, key)
