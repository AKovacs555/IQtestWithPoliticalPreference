import os
import sys
import pytest

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

import backend.db as db


class DummyResponse:
    def __init__(self, data=None):
        self.data = data
        self.error = None


class DummyTable:
    def __init__(self, rows):
        self.rows = rows
        self._select = False
        self._insert = None
        self._update = None
        self._filters = []
        self._single = False

    def select(self, *columns):
        self._select = True
        return self

    def insert(self, data):
        if isinstance(data, list):
            self.rows.extend(data)
        else:
            self.rows.append(data)
        return self

    def upsert(self, data):
        return self.insert(data)

    def update(self, data):
        self._update = data
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._insert is not None:
            data = self.rows
            self._reset()
            return DummyResponse(data)
        if self._update is not None:
            updated = []
            for r in self.rows:
                if all(r.get(col) == val for col, val in self._filters):
                    r.update(self._update)
                    updated.append(r)
            self._reset()
            return DummyResponse(updated)
        if self._select:
            res = [r for r in self.rows if all(r.get(col) == val for col, val in self._filters)]
            result = res[0] if self._single and res else res
            self._reset()
            return DummyResponse(result)
        self._reset()
        return DummyResponse(None)

    def _reset(self):
        self._select = False
        self._insert = None
        self._update = None
        self._filters = []
        self._single = False

    def or_(self, *args, **kwargs):  # minimal compatibility stub
        return self

    def limit(self, *args, **kwargs):  # minimal compatibility stub
        return self


class DummySupabase:
    def __init__(self):
        self.tables = {"app_users": [], "point_ledger": []}

    def table(self, name):
        if name not in self.tables:
            self.tables[name] = []
        return DummyTable(self.tables[name])

    def from_(self, name):
        return self.table(name)


@pytest.fixture
def fake_supabase(monkeypatch):
    supa = DummySupabase()
    monkeypatch.setattr("db.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("backend.db.get_supabase", lambda: supa, raising=False)
    return supa


def test_upsert_user_generates_random_username(fake_supabase):
    user_id = "u1"
    email = "user@example.com"
    db.upsert_user(user_id, email=email)
    rows = fake_supabase.tables["app_users"]
    assert rows[0]["email"] == email
    assert rows[0]["username"] != email
    assert "@" not in rows[0]["username"]


def test_upsert_user_replaces_username_with_at(fake_supabase):
    user_id = "u2"
    email = "user2@example.com"
    db.upsert_user(user_id, email=email)
    row = fake_supabase.tables["app_users"][0]
    row["username"] = "bad@name"
    db.upsert_user(user_id, email=email)
    assert "@" not in row["username"]
    assert row["username"] != "bad@name"
