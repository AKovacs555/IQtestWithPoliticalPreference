import os
import sys
import asyncio
from postgrest.exceptions import APIError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.routes import points as points_route
from backend.tests.conftest import DummySupabase, DummyTable


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
    monkeypatch.setattr(points_route, "get_supabase", lambda: fake_supabase)
    ledger = []
    monkeypatch.setattr(points_route, "insert_attempt_ledger", lambda *a: ledger.append(a))
    result = asyncio.run(points_route.get_points("u1"))
    assert result == {"points": 7}
    assert ledger == []


def test_missing_points_column_returns_zero(monkeypatch):
    supa = MissingPointsSupabase()
    supa.table("app_users").insert({"id": "u2", "hashed_id": "u2"}).execute()
    monkeypatch.setattr(points_route, "get_supabase", lambda: supa)
    monkeypatch.setattr(points_route, "insert_attempt_ledger", lambda *a: None)
    result = asyncio.run(points_route.get_points("u2"))
    assert result == {"points": 0}


def test_missing_row_creates_minimal(monkeypatch, fake_supabase):
    monkeypatch.setattr(points_route, "get_supabase", lambda: fake_supabase)
    ledger = []
    monkeypatch.setattr(points_route, "insert_attempt_ledger", lambda *a: ledger.append(a))
    result = asyncio.run(points_route.get_points("newuser"))
    assert result == {"points": 0}
    # Ensure minimal row created
    assert any(
        r["id"] == "newuser" and r.get("hashed_id") == "newuser"
        for r in fake_supabase.tables["app_users"]
    )
    assert ledger == [("newuser", 1, "signup")]
