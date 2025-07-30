import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    supabase_url = os.environ["SUPABASE_URL"]
    service_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(supabase_url, service_key)
