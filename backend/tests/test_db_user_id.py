import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend import db


def test_get_or_create_user_id_from_hashed_creates_and_retrieves():
    supa = db.get_supabase()
    hashed = "abc123"
    uid1 = db.get_or_create_user_id_from_hashed(supa, hashed)
    assert uid1 == hashed
    # Calling again should return same id
    uid2 = db.get_or_create_user_id_from_hashed(supa, hashed)
    assert uid1 == uid2 == hashed
    # Ensure the user row exists with hashed_id
    assert any(
        r["id"] == hashed and r["hashed_id"] == hashed for r in supa.tables["app_users"]
    )
