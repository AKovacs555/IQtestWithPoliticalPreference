import os
import sys
import asyncio
from postgrest.exceptions import APIError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.routes import points as points_route
from backend.tests.conftest import DummySupabase, DummyTable
from backend import db


class MissingPointsTable(DummyTable):
    def __init__(self, rows, name="app_users"):
        super().__init__(rows, name)
        self._selected = []

    def select(self, *columns):
        self._selected = list(columns)
        return super().select(*columns)

    def execute(self):
        if self._selected and "points" in self._selected:
            raise APIError(
                {
                    "message": "column points does not exist",
                    "details": "",
                    "hint": "",
                    "code": "42703",
                }
            )
        return super().execute()


class MissingPointsSupabase(DummySupabase):
    def table(self, name):
        if name not in self.tables:
            self.tables[name] = []
        if name == "app_users":
            return MissingPointsTable(self.tables[name], name)
        return super().table(name)


def test_points_column_exists_returns_value(monkeypatch, fake_supabase):
    fake_supabase.table("app_users").insert({"id": "u1", "hashed_id": "u1", "points": 7}).execute()
    fake_supabase.table("point_ledger").insert({"user_id": "u1", "delta": 1, "reason": "signup"}).execute()
    monkeypatch.setattr(points_route, "get_supabase", lambda: fake_supabase)
    calls = []
    monkeypatch.setattr(points_route.db, "insert_point_ledger", lambda *a, **k: calls.append(a))
    result = asyncio.run(points_route.get_points("u1"))
    assert result == {"points": 7}
    assert calls == []


def test_existing_user_awarded_when_missing_signup(monkeypatch, fake_supabase):
    fake_supabase.table("app_users").insert({"id": "u3", "hashed_id": "u3", "points": 7}).execute()
    monkeypatch.setattr(points_route, "get_supabase", lambda: fake_supabase)
    calls = []
    
    def mock_insert(uid, delta, reason="", expires_at=None):
        calls.append((uid, delta, reason))
        table = fake_supabase.tables["app_users"]
        for row in table:
            if row.get("id") == uid or row.get("hashed_id") == uid:
                row["points"] = row.get("points", 0) + delta
                break

    monkeypatch.setattr(points_route.db, "insert_point_ledger", mock_insert)
    result = asyncio.run(points_route.get_points("u3"))
    assert result == {"points": 8}
    assert calls == [("u3", 1, "signup")]


def test_missing_points_column_returns_zero(monkeypatch):
    supa = MissingPointsSupabase()
    supa.table("app_users").insert({"id": "u2", "hashed_id": "u2"}).execute()
    monkeypatch.setattr(points_route, "get_supabase", lambda: supa)
    monkeypatch.setattr(points_route.db, "insert_point_ledger", lambda *a, **k: None)
    result = asyncio.run(points_route.get_points("u2"))
    assert result == {"points": 0}


def test_missing_row_creates_minimal(monkeypatch, fake_supabase):
    monkeypatch.setattr(points_route, "get_supabase", lambda: fake_supabase)
    calls = []

    def mock_insert(uid, delta, reason="", expires_at=None):
        calls.append((uid, delta, reason))
        table = fake_supabase.tables["app_users"]
        for row in table:
            if row.get("id") == uid or row.get("hashed_id") == uid:
                row["points"] = row.get("points", 0) + delta
                break

    monkeypatch.setattr(points_route.db, "insert_point_ledger", mock_insert)
    result = asyncio.run(points_route.get_points("newuser"))
    assert result == {"points": 1}
    # Ensure minimal row created
    assert any(
        r["id"] == "newuser" and r.get("hashed_id") == "newuser"
        for r in fake_supabase.tables["app_users"]
    )
    assert calls == [("newuser", 1, "signup")]


def test_signup_reward_only_once(monkeypatch, fake_supabase):
    # Create user without granting signup reward
    db.create_user({"id": "u_new", "hashed_id": "u_new"})
    monkeypatch.setattr(points_route, "get_supabase", lambda: fake_supabase)
    first = asyncio.run(points_route.get_points("u_new"))
    second = asyncio.run(points_route.get_points("u_new"))
    assert first == {"points": 1}
    assert second == {"points": 1}
    ledger = [
        r for r in fake_supabase.tables["point_ledger"]
        if r["user_id"] == "u_new" and r["reason"] == "signup"
    ]
    assert len(ledger) == 1
