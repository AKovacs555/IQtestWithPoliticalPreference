import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

import types

irt_stub = types.ModuleType("irt")
irt_stub.prob_correct = lambda *a, **k: 0.0
irt_stub.percentile = lambda *a, **k: 0.0
sys.modules.setdefault("irt", irt_stub)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from backend.routes import quiz as quiz_module  # noqa: E402
from backend.routes import daily as daily_module  # noqa: E402

quiz_router = quiz_module.router
daily_router = daily_module.router


class _State:
    now = datetime(2023, 1, 1, 12, 0, 0)
    answers: list[dict] = []


def _setup(monkeypatch):
    app = FastAPI()
    app.state.sessions = {}
    app.include_router(quiz_router)
    app.include_router(daily_router)

    def fake_user():
        return {
            "hashed_id": "u1",
            "nationality": "US",
            "survey_completed": True,
            "demographic_completed": True,
        }

    app.dependency_overrides[daily_module.get_current_user] = fake_user
    app.dependency_overrides[quiz_module.get_current_user] = fake_user
    client = TestClient(app)

    # patch datetime
    class FakeDateTime(datetime):
        @classmethod
        def utcnow(cls):
            return _State.now

    monkeypatch.setattr("backend.routes.daily.datetime", FakeDateTime)
    monkeypatch.setattr("backend.routes.quiz.datetime", FakeDateTime)

    # patch DB helpers
    def fake_count(user_id, day):
        return sum(1 for r in _State.answers if r["user_id"] == user_id and r["day"] == day)

    def fake_insert(user_id, qid, answer):
        _State.answers.append({"user_id": user_id, "qid": qid, "day": _State.now.date()})

    monkeypatch.setattr("backend.routes.daily.get_daily_answer_count", fake_count)
    monkeypatch.setattr("backend.routes.daily.insert_daily_answer", fake_insert)
    monkeypatch.setattr("backend.routes.quiz.get_daily_answer_count", fake_count)

    # patch quiz question generation and supabase
    monkeypatch.setattr(
        "backend.routes.quiz.get_balanced_random_questions_by_set",
        lambda n, set_id, lang=None: [
            {"id": "1", "question": "Q1", "options": ["a", "b"], "answer": 0,
             "image": None, "option_images": []}
        ],
    )
    class DummyTable:
        def insert(self, data):
            return self

        def execute(self):
            class R:
                data = []
            return R()

    class DummySupabase:
        def table(self, name):
            return DummyTable()

    monkeypatch.setattr("backend.routes.quiz.get_supabase_client", lambda: DummySupabase())

    # reduce number of questions
    monkeypatch.setattr("backend.routes.quiz.NUM_QUESTIONS", 1, raising=False)

    return client


def test_quiz_start_blocked_until_three(monkeypatch, caplog):
    _State.now = datetime(2023, 1, 1, 12, 0, 0)
    _State.answers.clear()
    client = _setup(monkeypatch)

    r = client.get("/daily/quota")
    assert r.status_code == 200
    assert r.json()["answered"] == 0

    for i in range(2):
        client.post("/daily/answer", json={"question_id": str(i), "answer": {}})

    with caplog.at_level("ERROR"):
        res = client.get("/quiz/start?set_id=s1")
    assert res.status_code == 403
    data = res.json()["detail"]
    assert data["code"] == "DAILY3_REQUIRED"
    assert data["remaining"] == 1
    assert "daily3_block" in caplog.text


def test_quiz_start_allows_after_three(monkeypatch, caplog):
    _State.now = datetime(2023, 1, 1, 12, 0, 0)
    _State.answers.clear()
    client = _setup(monkeypatch)

    for i in range(3):
        client.post("/daily/answer", json={"question_id": str(i), "answer": {}})

    q = client.get("/daily/quota")
    assert q.json()["answered"] == 3

    with caplog.at_level("INFO"):
        res = client.get("/quiz/start?set_id=s1")
    assert res.status_code == 200
    assert res.json()["session_id"]
    assert "quiz_start_allowed" in caplog.text


def test_quota_resets_next_day(monkeypatch, caplog):
    _State.now = datetime(2023, 1, 1, 12, 0, 0)
    _State.answers.clear()
    client = _setup(monkeypatch)

    for i in range(3):
        client.post("/daily/answer", json={"question_id": str(i), "answer": {}})

    _State.now = _State.now + timedelta(days=1)

    with caplog.at_level("INFO"):
        resp = client.get("/daily/quota")
    data = resp.json()
    assert data["answered"] == 0
    assert "daily3_reset_detected" in caplog.text
    expected_reset = (
        datetime.combine(_State.now.date(), datetime.min.time()) + timedelta(days=1)
    ).isoformat() + "Z"
    assert data["reset_at"] == expected_reset
