import os, sys, uuid
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import backend.routes.quiz as quiz
from backend.routes.quiz import router, get_current_user


def make_app(monkeypatch, supa, duration=25):
    app = FastAPI()
    app.include_router(router)
    app.state.sessions = {}
    app.dependency_overrides[get_current_user] = lambda: {
        "hashed_id": str(uuid.uuid4()),
        "nationality": "JP",
        "survey_completed": True,
        "demographic_completed": True,
    }
    monkeypatch.setenv("QUIZ_DURATION_MINUTES", str(duration))
    monkeypatch.setattr(quiz, "NUM_QUESTIONS", 1)
    monkeypatch.setattr(
        quiz,
        "get_balanced_random_questions_by_set",
        lambda n, set_id, lang=None: [
            {"id": 1, "answer": 0, "options": ["0", "1"], "irt_a": 1.0, "irt_b": 0.0}
        ],
    )
    monkeypatch.setattr(quiz, "get_supabase_client", lambda: supa)
    return app


def test_session_timeout(monkeypatch, fake_supabase):
    app = make_app(monkeypatch, fake_supabase, duration=25)
    with TestClient(app) as client:
        start = client.get("/quiz/start?set_id=x").json()
        sid = start["session_id"]
        fake_supabase.table("quiz_sessions").update(
            {"expires_at": (datetime.utcnow() - timedelta(seconds=1)).isoformat()}
        ).eq("id", sid).execute()
        resp = client.post(
            "/quiz/submit",
            json={"session_id": sid, "answers": [{"id": 1, "answer": 0}]},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Session expired"
        row = quiz.get_supabase_client().table("quiz_sessions").select("*").eq("id", sid).single().execute().data
        assert row["status"] == "timeout"


def test_double_submit(monkeypatch, fake_supabase):
    app = make_app(monkeypatch, fake_supabase, duration=25)
    with TestClient(app) as client:
        start = client.get("/quiz/start?set_id=x").json()
        sid = start["session_id"]
        answers = [{"id": 1, "answer": 0}]
        first = client.post("/quiz/submit", json={"session_id": sid, "answers": answers})
        assert first.status_code == 200
        second = client.post("/quiz/submit", json={"session_id": sid, "answers": answers})
        assert second.status_code == 400
        row = quiz.get_supabase_client().table("quiz_sessions").select("*").eq("id", sid).single().execute().data
        assert row["status"] == "submitted"
