import os
import sys
from datetime import date
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app
from backend.deps.auth import create_token


def _seed_items(supa, count=5):
    supa.tables.setdefault("survey_items", [])
    for i in range(1, count + 1):
        supa.tables["survey_items"].append({
            "id": f"i{i}",
            "survey_id": "s1",
            "body": f"Q{i}",
            "choices": ["a", "b"],
            "order_no": i,
            "lang": "ja",
            "is_active": True,
        })


def _create_user(supa, uid: str):
    supa.tables.setdefault("users", []).append({"hashed_id": uid})


def test_daily_quota_enforced(fake_supabase):
    _seed_items(fake_supabase, 5)
    _create_user(fake_supabase, "uquota")
    today = date.today().isoformat()
    fake_supabase.tables.setdefault("survey_responses", []).extend([
        {"id": "r1", "user_id": "uquota", "item_id": "i1", "answer_index": 0, "answered_on": today},
        {"id": "r2", "user_id": "uquota", "item_id": "i2", "answer_index": 0, "answered_on": today},
    ])
    token = create_token("uquota")
    with TestClient(app) as client:
        r1 = client.post(
            "/surveys/answer",
            json={"item_id": "i3", "answer_index": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200
        r2 = client.post(
            "/surveys/answer",
            json={"item_id": "i4", "answer_index": 0},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 409
        assert r2.json()["detail"]["error"] == "daily_quota_exceeded"


def test_daily_quota_get_after_limit(fake_supabase):
    _seed_items(fake_supabase, 5)
    _create_user(fake_supabase, "uquota2")
    today = date.today().isoformat()
    fake_supabase.tables.setdefault("survey_responses", []).extend([
        {"id": "r1", "user_id": "uquota2", "item_id": "i1", "answer_index": 0, "answered_on": today},
        {"id": "r2", "user_id": "uquota2", "item_id": "i2", "answer_index": 0, "answered_on": today},
        {"id": "r3", "user_id": "uquota2", "item_id": "i3", "answer_index": 0, "answered_on": today},
    ])
    token = create_token("uquota2")
    with TestClient(app) as client:
        r = client.get("/surveys/daily3", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 409
        assert r.json()["detail"]["error"] == "daily_quota_exceeded"
