from fastapi import FastAPI
from fastapi.testclient import TestClient
import os
import sys
from types import SimpleNamespace
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import backend.routes.quiz as quiz
from backend.routes.quiz import router, get_current_user


def test_submit_quiz_handles_missing_user_scores(monkeypatch):
    app = FastAPI()
    app.include_router(router)
    app.state.sessions = {"sess1": {1: {"answer": 0, "a": 1.0, "b": 0.0}}}
    app.state.session_expires = {"sess1": datetime.utcnow() + timedelta(minutes=5)}
    app.state.session_started = {"sess1": datetime.utcnow()}
    app.dependency_overrides[get_current_user] = lambda: {"hashed_id": "u1"}

    class DummyTable:
        def __init__(self, name):
            self.name = name

        def select(self, *args, **kwargs):
            return self

        def insert(self, data):
            return self

        def single(self):
            return self

        def update(self, data):
            return self

        def eq(self, *args, **kwargs):
            return self

        def execute(self):
            if self.name == "user_scores":
                raise Exception("missing table")
            return SimpleNamespace(data=None)

    class DummySupabase:
        def from_(self, name):
            return DummyTable(name)

        table = from_

    monkeypatch.setattr(quiz, "get_supabase_client", lambda: DummySupabase())
    monkeypatch.setattr(quiz, "generate_share_image", lambda uid, iq, pct: "")

    client = TestClient(app)
    payload = {"session_id": "sess1", "answers": [{"id": 1, "answer": 0}]}
    resp = client.post("/quiz/submit", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "iq" in data
    assert "percentile" in data
