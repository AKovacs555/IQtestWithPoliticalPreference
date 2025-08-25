import os
import sys
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

import backend.routes.surveys as surveys_module  # noqa: E402


class _State:
    now = datetime(2023, 1, 1, 12, 0, 0)
    answers: list[dict] = []


def _setup(monkeypatch):
    app = FastAPI()
    app.include_router(surveys_module.router)

    def fake_user():
        return {
            "hashed_id": "u1",
            "nationality": "US",
            "survey_completed": True,
            "demographic_completed": True,
        }

    app.dependency_overrides[surveys_module.get_current_user] = fake_user
    client = TestClient(app)

    class FakeDateTime(datetime):
        @classmethod
        def utcnow(cls):
            return _State.now

        @classmethod
        def now(cls, tz=None):
            return _State.now if tz is None else _State.now.astimezone(tz)

    monkeypatch.setattr("backend.routes.surveys.datetime", FakeDateTime)

    def fake_count(user_id, day=None):
        return sum(
            1
            for r in _State.answers
            if r["user_id"] == user_id and (day is None or r["day"] == day)
        )

    def fake_insert(user_id, qid):
        _State.answers.append({"user_id": user_id, "qid": qid, "day": _State.now.date()})

    monkeypatch.setattr("backend.db.get_daily_answer_count", fake_count)
    monkeypatch.setattr("backend.db.insert_daily_answer", fake_insert)

    calls: list[tuple[str, int, str]] = []
    monkeypatch.setattr(
        "backend.db.insert_point_ledger",
        lambda uid, pts, reason="": calls.append((uid, pts, reason)),
    )
    updated: dict = {}

    def fake_update(_supa, uid, data):
        updated[uid] = data

    monkeypatch.setattr("backend.db.update_user", fake_update)
    monkeypatch.setattr("backend.routes.surveys.get_supabase_client", lambda: object())
    monkeypatch.setattr(
        "backend.routes.surveys.get_setting_int", lambda _s, _k, default=1: 1
    )
    return client, calls, updated


def test_surveys_answer_grants_points(monkeypatch):
    _State.now = datetime(2023, 1, 1, 12, 0, 0)
    _State.answers.clear()
    client, calls, updated = _setup(monkeypatch)
    for i in range(3):
        res = client.post("/surveys/answer", json={"item_id": str(i), "answer_index": 0})
        assert res.status_code == 200
    assert calls == [("u1", 1, "daily3")]
    assert updated.get("u1") == {"survey_completed": True}
