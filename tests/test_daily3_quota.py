import os
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

# Ensure modules import correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.deps.auth import create_token
import backend.routes.quiz as quiz
from backend.tests.conftest import DummySupabase


@pytest.fixture(autouse=True)
def fake_supabase(monkeypatch):
    monkeypatch.setenv("DAILY3_TEST_REAL", "1")
    supa = DummySupabase()
    monkeypatch.setattr("db.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("backend.db.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("main.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("backend.utils.settings.supabase", supa, raising=False)
    monkeypatch.setattr("backend.routes.settings.supabase", supa, raising=False)
    return supa


@pytest.fixture(autouse=True)
def patch_quiz(monkeypatch, fake_supabase):
    monkeypatch.setattr(quiz, "NUM_QUESTIONS", 1)
    monkeypatch.setattr(quiz, "get_supabase_client", lambda: fake_supabase)
    monkeypatch.setattr(
        quiz,
        "get_balanced_random_questions_by_set",
        lambda n, set_id, lang=None: [
            {"id": "q1", "question": "Q1", "options": ["a", "b"]}
        ],
    )


def _create_user(supa, uid):
    supa.tables.setdefault("app_users", []).append(
        {
            "hashed_id": uid,
            "nationality": "JP",
            "survey_completed": True,
            "demographic_completed": True,
        }
    )


def _auth_header(uid):
    return {"Authorization": f"Bearer {create_token(uid)}"}


def test_quiz_start_blocked_until_three(fake_supabase, monkeypatch, caplog):
    _create_user(fake_supabase, "u1")
    with TestClient(app) as client:
        r = client.get("/daily/quota", headers=_auth_header("u1"))
        assert r.json()["answered"] == 0
        for i in range(2):
            client.post(
                "/daily/answer",
                json={"item_id": f"i{i}", "answer_index": 0},
                headers=_auth_header("u1"),
            )
        caplog.clear()
        resp = client.get("/quiz/start?set_id=x", headers=_auth_header("u1"))
        assert resp.status_code == 403
        body = resp.json()
        assert body["detail"]["code"] == "DAILY3_REQUIRED"
        assert body["detail"]["remaining"] == 1
        assert any("daily3_block" in rec.message for rec in caplog.records)


def test_quiz_start_allows_after_three(fake_supabase, monkeypatch, caplog):
    _create_user(fake_supabase, "u2")
    with TestClient(app) as client:
        for i in range(3):
            client.post(
                "/daily/answer",
                json={"item_id": f"a{i}", "answer_index": 0},
                headers=_auth_header("u2"),
            )
        q = client.get("/daily/quota", headers=_auth_header("u2")).json()
        assert q["answered"] == 3
        caplog.clear()
        resp = client.get("/quiz/start?set_id=x", headers=_auth_header("u2"))
        assert resp.status_code == 200
        assert any("quiz_start_allowed" in rec.message for rec in caplog.records)


def test_quota_resets_next_day(fake_supabase, monkeypatch, caplog):
    _create_user(fake_supabase, "u3")
    day1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr("backend.routes.daily._utc_now", lambda: day1)
    with TestClient(app) as client:
        for i in range(3):
            client.post(
                "/daily/answer",
                json={"item_id": f"b{i}", "answer_index": 0},
                headers=_auth_header("u3"),
            )
    day2 = day1 + timedelta(days=1)
    monkeypatch.setattr("backend.routes.daily._utc_now", lambda: day2)
    with TestClient(app) as client:
        caplog.clear()
        q = client.get("/daily/quota", headers=_auth_header("u3")).json()
        assert q["answered"] == 0
        assert any("daily3_reset_detected" in rec.message for rec in caplog.records)

