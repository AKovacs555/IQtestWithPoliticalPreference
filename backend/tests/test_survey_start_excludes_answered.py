import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app
from backend.deps.auth import create_token


def test_survey_start_excludes_answered(fake_supabase):
    # Seed survey and items
    survey = {
        "id": "s1",
        "group_id": "g1",
        "title": "t",
        "question_text": "q",
        "lang": "en",
        "status": "approved",
        "is_active": True,
    }
    fake_supabase.tables.setdefault("surveys", []).append(survey)
    fake_supabase.tables.setdefault("survey_items", []).append(
        {"id": "i1", "survey_id": "s1", "body": "A", "position": 1, "lang": "en"}
    )

    # Create user
    fake_supabase.tables.setdefault("app_users", []).append(
        {"id": "u1", "hashed_id": "hash1", "nationality": "AF"}
    )
    token = create_token("u1")
    client = TestClient(app)

    # First start should return the survey
    r1 = client.get(
        "/survey/start?lang=en", headers={"Authorization": f"Bearer {token}"}
    )
    assert r1.status_code == 200
    assert r1.json()["survey"]["id"] == "s1"

    # Record an answer using raw user id
    fake_supabase.table("survey_answers").insert(
        {
            "survey_group_id": "g1",
            "survey_id": "s1",
            "survey_item_id": "i1",
            "user_id": "u1",
        }
    ).execute()

    # Subsequent start should not return the same survey
    r2 = client.get(
        "/survey/start?lang=en", headers={"Authorization": f"Bearer {token}"}
    )
    assert r2.status_code == 404
