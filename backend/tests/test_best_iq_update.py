import os
import sys
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import backend.routes.quiz as quiz
from backend.routes.quiz import router, get_current_user


def setup_app(monkeypatch, supa):
    app = FastAPI()
    app.include_router(router)
    app.state.sessions = {}
    app.state.session_expires = {}
    app.state.session_started = {}
    app.dependency_overrides[get_current_user] = lambda: {"hashed_id": "u1"}
    monkeypatch.setattr(quiz, "NUM_QUESTIONS", 1)
    monkeypatch.setattr(
        quiz,
        "get_balanced_random_questions_by_set",
        lambda n, set_id, lang=None: [
            {"id": 1, "answer": 0, "options": ["0", "1"], "irt_a": 1.0, "irt_b": 0.0}
        ],
    )
    monkeypatch.setattr(quiz, "get_supabase_client", lambda: supa)
    monkeypatch.setattr(quiz, "get_daily_answer_count", lambda uid, day=None: 3)
    monkeypatch.setattr(quiz, "spend_points", lambda uid, amt=1, reason="consume": 0)
    monkeypatch.setattr(quiz, "estimate_theta", lambda responses: 0.0)
    monkeypatch.setattr(quiz, "percentile", lambda theta, dist: 50)
    monkeypatch.setattr(quiz, "ability_summary", lambda theta: "")
    monkeypatch.setattr(quiz, "standard_error", lambda theta, responses: 0.0)
    monkeypatch.setattr(quiz, "generate_share_image", lambda uid, iq, pct: "")
    return app


def _submit(app, client, iq, monkeypatch):
    monkeypatch.setattr(quiz, "iq_score", lambda theta: iq)
    sid = f"sess{iq}"
    app.state.sessions[sid] = {1: {"answer": 0, "a": 1.0, "b": 0.0}}
    app.state.session_expires[sid] = datetime.utcnow() + timedelta(minutes=5)
    app.state.session_started[sid] = datetime.utcnow()
    payload = {"attempt_id": sid, "answers": [{"id": 1, "answer": 0}]}
    resp = client.post("/quiz/submit", json=payload)
    assert resp.status_code == 200


def test_user_best_iq_updates(monkeypatch, fake_supabase):
    app = setup_app(monkeypatch, fake_supabase)
    with TestClient(app) as client:
        _submit(app, client, 100, monkeypatch)
        row = (
            fake_supabase.table("user_best_iq")
            .select("*")
            .eq("user_id", "u1")
            .single()
            .execute()
            .data
        )
        assert row["best_iq"] == 100
        _submit(app, client, 80, monkeypatch)
        row = (
            fake_supabase.table("user_best_iq")
            .select("*")
            .eq("user_id", "u1")
            .single()
            .execute()
            .data
        )
        assert row["best_iq"] == 100
        _submit(app, client, 130, monkeypatch)
        row = (
            fake_supabase.table("user_best_iq")
            .select("*")
            .eq("user_id", "u1")
            .single()
            .execute()
            .data
        )
        assert row["best_iq"] == 130
