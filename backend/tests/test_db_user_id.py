import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend import db


def test_get_or_create_user_id_from_hashed_creates_and_retrieves():
    supa = db.get_supabase()
    hashed = 'abc123'
    uid1 = db.get_or_create_user_id_from_hashed(supa, hashed)
    assert uuid.UUID(uid1)  # valid UUID
    # Calling again should return same id
    uid2 = db.get_or_create_user_id_from_hashed(supa, hashed)
    assert uid1 == uid2
    # Ensure the user row exists with hashed_id
    assert any(r['id'] == uid1 and r['hashed_id'] == hashed for r in supa.tables['users'])
