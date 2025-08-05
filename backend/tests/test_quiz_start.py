from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys, os

# Ensure the backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import backend.routes.quiz as quiz
from backend.routes.quiz import router, get_current_user


def test_start_quiz_falls_back_to_local_questions(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    app.state.sessions = {}
    app.dependency_overrides[get_current_user] = lambda: {
        "hashed_id": "u1",
        "nationality": "US",
        "survey_completed": True,
    }

    def fail_client():
        raise RuntimeError("missing supabase")

    monkeypatch.setattr(quiz, "get_supabase_client", fail_client)

    client = TestClient(app)
    resp = client.get("/quiz/start")
    assert resp.status_code == 200
    data = resp.json()
    assert data["questions"], "should return fallback questions"
    assert len(data["questions"]) <= quiz.NUM_QUESTIONS
