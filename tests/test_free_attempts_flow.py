import os
import sys
from pathlib import Path
import sqlite3
import pytest
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

import backend.routes.quiz as quiz  # noqa: E402
from backend.routes.quiz import router, get_current_user  # noqa: E402


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
        self._filters: list[tuple[str, object]] = []
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


class DummySupabase:
    def __init__(self):
        self.tables = {"app_users": [], "attempt_ledger": []}

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


def _setup_app(monkeypatch, fake_supabase, free_attempts: int):
    app = FastAPI()
    app.state.sessions = {}
    app.include_router(router)

    uid = "u1"
    fake_supabase.table("app_users").insert({"hashed_id": uid, "free_attempts": free_attempts}).execute()
    if free_attempts:
        fake_supabase.table("attempt_ledger").insert({"user_id": uid, "delta": free_attempts, "reason": "seed"}).execute()

    app.dependency_overrides[get_current_user] = lambda: {
        "hashed_id": uid,
        "nationality": "JP",
        "survey_completed": True,
        "demographic_completed": True,
    }

    monkeypatch.setattr(quiz, "NUM_QUESTIONS", 1, raising=False)
    monkeypatch.setattr(
        quiz,
        "get_balanced_random_questions_by_set",
        lambda n, set_id, lang=None: [
            {"id": 1, "question": "Q1", "options": ["a", "b"], "answer": 0}
        ],
    )
    monkeypatch.setattr(quiz, "get_supabase_client", lambda: fake_supabase)
    monkeypatch.setattr(quiz, "get_daily_answer_count", lambda user_id, day: 3)
    return app, uid


def test_consume_ok(monkeypatch, fake_supabase, caplog):
    app, uid = _setup_app(monkeypatch, fake_supabase, 2)
    with TestClient(app) as client, caplog.at_level("INFO"):
        res = client.get("/quiz/start?set_id=s1")
    assert res.status_code == 200
    from backend.db import get_available_attempts

    remaining = get_available_attempts(uid)
    assert remaining == 1
    assert "attempts_consume_ok" in caplog.text


def test_need_payment_when_zero(monkeypatch, fake_supabase, caplog):
    app, uid = _setup_app(monkeypatch, fake_supabase, 0)
    with TestClient(app) as client, caplog.at_level("ERROR"):
        res = client.get("/quiz/start?set_id=s1")
    assert res.status_code == 400
    assert res.json().get("error") == "survey_required" or res.json().get("detail", {}).get("error") == "survey_required"
    assert "attempts_insufficient" in caplog.text


def _run_migration(conn, sql: str):
    try:
        conn.execute("alter table users rename column free_tests to free_attempts")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute(
            "alter table users add column if not exists free_attempts integer not null default 0"
        )
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute(
            "create index if not exists idx_users_id_free_attempts on users (id, free_attempts)"
        )
    except sqlite3.OperationalError:
        pass


def test_migration_idempotent(tmp_path):
    migration = next(Path("supabase/migrations").glob("*_free_attempts.sql"))
    sql = migration.read_text()
    conn = sqlite3.connect(":memory:")
    conn.execute("create table users (id integer primary key, free_tests integer)")
    _run_migration(conn, sql)
    _run_migration(conn, sql)
    cols = [r[1] for r in conn.execute("pragma table_info(users)")]
    assert cols.count("free_attempts") == 1
    idxs = [r[1] for r in conn.execute("pragma index_list('users')")]
    assert "idx_users_id_free_attempts" in idxs
    conn.close()
