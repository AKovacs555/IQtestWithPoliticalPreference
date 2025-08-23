import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from main import app
from backend.deps import auth as auth_deps
from backend.deps.auth import create_token
from backend import db
import backend.routes.admin_users as admin_users_route
import routes.admin_users as admin_users_route_pkg


@pytest.mark.parametrize("query", ["user@", "example.com"])
def test_search_users_handles_special_chars(monkeypatch, fake_supabase, query):
    fake_supabase.table("app_users").insert({
        "hashed_id": "u1",
        "email": "user@example.com",
        "display_name": "User",
        "points": 0,
    }).execute()

    token = create_token("admin", is_admin=True)
    monkeypatch.setattr(db, "get_user", lambda _id: {"hashed_id": "admin", "is_admin": True})
    monkeypatch.setattr(auth_deps, "get_user", lambda _id: {"hashed_id": "admin", "is_admin": True})
    monkeypatch.setattr(db, "get_points", lambda _id: 0)
    monkeypatch.setattr(auth_deps, "get_points", lambda _id: 0)
    monkeypatch.setattr(admin_users_route, "get_supabase", lambda: fake_supabase)
    monkeypatch.setattr(admin_users_route_pkg, "get_supabase", lambda: fake_supabase)

    with TestClient(app) as client:
        r = client.get(
            "/admin/users/search",
            params={"query": query},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    assert any(u["email"] == "user@example.com" for u in r.json().get("users", []))
