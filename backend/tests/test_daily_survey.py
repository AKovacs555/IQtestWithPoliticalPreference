import os
import sys
from datetime import date
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app
from backend.deps.auth import create_token


def _seed_items(supa, count=3):
    survey_id = "s1"
    supa.tables.setdefault("survey_items", [])
    for i in range(1, count + 1):
        supa.tables["survey_items"].append({
            "id": f"i{i}",
            "survey_id": survey_id,
            "body": f"Q{i}",
            "choices": ["a", "b"],
            "order_no": i,
            "lang": "ja",
            "is_active": True,
        })
    return survey_id


def _create_user(supa, uid: str):
    supa.tables.setdefault("users", []).append({"hashed_id": uid})


def test_daily3_skips_answered(fake_supabase):
    _seed_items(fake_supabase)
    _create_user(fake_supabase, "u1")
    fake_supabase.tables.setdefault("survey_responses", []).append({
        "id": "r1",
        "user_id": "u1",
        "item_id": "i1",
        "answer_index": 0,
        "answered_on": date.today().isoformat(),
    })
    token = create_token("u1")
    with TestClient(app) as client:
        r = client.get("/surveys/daily3", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        ids = {i["id"] for i in data["items"]}
        assert "i1" not in ids


def test_answer_unique_per_day(fake_supabase):
    _seed_items(fake_supabase, 1)
    _create_user(fake_supabase, "u2")
    token = create_token("u2")
    with TestClient(app) as client:
        r1 = client.post(
            "/surveys/answer",
            json={"item_id": "i1", "answer_index": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        r2 = client.post(
            "/surveys/answer",
            json={"item_id": "i1", "answer_index": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 409
        assert r2.json()["detail"]["error"] == "already_answered"
    responses = fake_supabase.tables.get("survey_responses", [])
    assert len(responses) == 1
    assert responses[0]["answer_index"] == 0


def test_daily3_returns_remaining(fake_supabase):
    _seed_items(fake_supabase, 2)
    _create_user(fake_supabase, "u3")
    token = create_token("u3")
    with TestClient(app) as client:
        r = client.get("/surveys/daily3", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 2
