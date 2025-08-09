import os
import sys
import logging
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))
import backend.routes.quiz as quiz  # noqa: E402
from backend.routes.quiz import router, get_current_user  # noqa: E402
import backend.tests.conftest as backend_conftest  # noqa: E402


@pytest.fixture
def fake_supabase(monkeypatch):
    return backend_conftest.fake_supabase.__wrapped__(monkeypatch)


def make_app(monkeypatch, supabase, free_attempts):
    app = FastAPI()
    app.include_router(router)
    app.state.sessions = {}
    app.dependency_overrides[get_current_user] = lambda: {
        "hashed_id": "u1",
        "nationality": "JP",
        "survey_completed": True,
        "demographic_completed": True,
    }
    monkeypatch.setattr(quiz, "NUM_QUESTIONS", 1)
    monkeypatch.setattr(
        quiz,
        "get_balanced_random_questions_by_set",
        lambda n, set_id, lang=None: [
            {"id": 1, "answer": 0, "options": ["0", "1"], "irt_a": 1.0, "irt_b": 0.0}
        ],
    )
    monkeypatch.setattr(quiz, "get_random_pending_surveys", lambda *a, **k: [])
    monkeypatch.setattr(quiz, "get_supabase_client", lambda: supabase)
    supabase.table("app_users").insert({"hashed_id": "u1", "free_attempts": free_attempts}).execute()
    return app


def test_consume_ok(monkeypatch, fake_supabase, caplog):
    app = make_app(monkeypatch, fake_supabase, 2)
    with TestClient(app) as client:
        with caplog.at_level(logging.INFO):
            resp = client.get("/quiz/start?set_id=x")
    assert resp.status_code == 200
    row = fake_supabase.tables["app_users"][0]
    assert row["free_attempts"] == 1
    assert any(
        r.message == "attempts_consume_ok" and r.user_id == "u1" and r.remaining == 1
        for r in caplog.records
    )


def test_need_payment_when_zero(monkeypatch, fake_supabase, caplog):
    app = make_app(monkeypatch, fake_supabase, 0)
    with TestClient(app) as client:
        with caplog.at_level(logging.INFO):
            resp = client.get("/quiz/start?set_id=x")
    assert resp.status_code == 402
    assert resp.json() == {"code": "NEED_PAYMENT"}
    row = fake_supabase.tables["app_users"][0]
    assert row["free_attempts"] == 0
    assert any(r.message == "attempts_insufficient" and r.user_id == "u1" for r in caplog.records)


def test_migration_idempotent():
    sql = Path("supabase/migrations/20250909_free_attempts.sql").read_text().lower()
    # Ensure defensive clauses exist
    assert "if not exists" in sql
    assert "if exists" in sql
