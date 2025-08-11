import os
from supabase import create_client, Client

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_API_KEY')
if not url or not key:
    raise RuntimeError('Missing Supabase credentials')

supabase_admin: Client = create_client(url, key)
