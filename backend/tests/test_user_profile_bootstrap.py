import types

import backend.db as db
from backend.routes import user_profile_bootstrap as upb


def test_ensure_profile_sets_username_and_email(fake_supabase, monkeypatch):
    fake_supabase.auth = types.SimpleNamespace(
        admin=types.SimpleNamespace(update_user_by_id=lambda *a, **k: None)
    )
    monkeypatch.setattr(
        upb, "decode_supabase_jwt", lambda token: {"sub": "u42", "email": "u42@example.com"}
    )
    monkeypatch.setattr(upb, "supabase_admin", fake_supabase, raising=False)

    resp = upb.ensure_profile(authorization="Bearer token")
    assert resp == {"ok": True, "is_admin": False}

    row = fake_supabase.tables["app_users"][0]
    assert row["email"] == "u42@example.com"
    adj, animal = row["username"].split(" ", 1)
    assert adj in db._ADJECTIVES
    assert animal in db._DUMB_ANIMALS
