import os
import sys
from datetime import date
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app
from backend.deps.auth import create_token
from backend.routes.dependencies import require_admin


def _create_user(supa, uid: str):
    supa.tables.setdefault("app_users", []).append({"hashed_id": uid})


def _seed_survey(supa, *, language="en", status="pending", selection_type="single"):
    survey = {
        "id": "s1",
        "survey_group_id": "g1",
        "title": "t",
        "question_text": "q1",
        "language": language,
        "allowed_countries": ["JP"],
        "selection_type": selection_type,
        "status": status,
    }
    supa.tables.setdefault("surveys", []).append(survey)
    options = [
        {
            "id": "o1",
            "survey_id": "s1",
            "option_text": "A",
            "order": 1,
            "is_exclusive": False,
            "requires_text": False,
            "option_group_id": "og1",
        },
        {
            "id": "o2",
            "survey_id": "s1",
            "option_text": "Other",
            "order": 2,
            "is_exclusive": False,
            "requires_text": True,
            "option_group_id": "og2",
        },
    ]
    supa.tables.setdefault("survey_options", []).extend(options)
    return survey, options


def test_admin_crud_and_user_flow(fake_supabase):
    app.dependency_overrides[require_admin] = lambda: True
    client = TestClient(app)

    payload = {
        "title": "Title",
        "question_text": "What?",
        "language": "en",
        "allowed_countries": ["JP"],
        "selection_type": "single",
        "status": "pending",
        "options": [
            {"text": "Yes", "is_exclusive": False, "requires_text": False, "order": 1},
            {"text": "No", "is_exclusive": False, "requires_text": False, "order": 2},
        ],
    }
    r = client.post("/admin/surveys", json=payload)
    assert r.status_code == 200
    survey_id = r.json()["id"]

    upd = dict(payload)
    upd["question_text"] = "Updated?"
    upd["options"][0]["text"] = "Sure"
    client.put(f"/admin/surveys/{survey_id}", json=upd)

    client.post(f"/admin/surveys/{survey_id}/approve")
    assert fake_supabase.tables["surveys"][0]["status"] == "approved"

    token = create_token("u1")
    _create_user(fake_supabase, "u1")
    r = client.get(
        "/surveys/available?lang=en&country=JP",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    opt_id = data[0]["options"][0]["option_id"]

    client.post(
        f"/surveys/{survey_id}/respond",
        json={"option_ids": [opt_id], "other_texts": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(fake_supabase.tables.get("survey_responses", [])) == 1

    r = client.get(
        "/surveys/available?lang=en&country=JP",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json() == []

    fake_supabase.tables.setdefault("survey_option_iq_stats", []).append(
        {
            "survey_id": survey_id,
            "option_id": opt_id,
            "option_text": "Sure",
            "responses_count": 1,
            "avg_iq": 100,
        }
    )
    r = client.get(f"/surveys/{survey_id}/stats")
    assert r.status_code == 200
    assert r.json()[0]["avg_iq"] == 100

    client.delete(f"/admin/surveys/{survey_id}")
    assert fake_supabase.tables.get("surveys") == []


def test_multiple_choice_submission(fake_supabase):
    app.dependency_overrides[require_admin] = lambda: True
    client = TestClient(app)
    # seed survey with multiple selection
    survey, options = _seed_survey(fake_supabase, selection_type="multiple", status="approved")
    token = create_token("u2")
    _create_user(fake_supabase, "u2")
    r = client.get(
        "/surveys/available?lang=en&country=JP",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    opt_ids = [o["id"] for o in options]
    payload = {"option_ids": opt_ids, "other_texts": {opt_ids[1]: "text"}}
    client.post(
        f"/surveys/{survey['id']}/respond",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    responses = fake_supabase.tables.get("survey_responses", [])
    assert len(responses) == 2
    assert any(r.get("other_text") == "text" for r in responses)

