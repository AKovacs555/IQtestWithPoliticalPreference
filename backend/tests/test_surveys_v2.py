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


def _seed_survey(supa, *, lang="en", is_single=True, status="approved"):
    survey = {
        "id": "s1",
        "title": "t",
        "question_text": "q1",
        "lang": lang,
        "allowed_countries": ["JP"],
        "is_single_choice": is_single,
        "status": status,
        "is_active": True,
    }
    supa.tables.setdefault("surveys", []).append(survey)
    items = [
        {
            "id": "o1",
            "survey_id": "s1",
            "statement": "A",
            "position": 1,
            "is_exclusive": False,
        },
        {
            "id": "o2",
            "survey_id": "s1",
            "statement": "Other",
            "position": 2,
            "is_exclusive": False,
        },
    ]
    supa.tables.setdefault("survey_items", []).extend(items)
    return survey, items


def test_admin_crud_and_user_flow(fake_supabase):
    app.dependency_overrides[require_admin] = lambda: True
    client = TestClient(app)

    payload = {
        "title": "Title",
        "question_text": "What?",
        "lang": "en",
        "allowed_countries": ["JP"],
        "selection": "sa",
        "exclusive_indexes": [],
        "choices": ["Yes", "No"],
    }
    r = client.post("/admin/surveys", json=payload)
    assert r.status_code == 200
    survey_id = r.json()["id"]

    upd = dict(payload)
    upd["question_text"] = "Updated?"
    upd["choices"][0] = "Sure"
    client.put(f"/admin/surveys/{survey_id}", json=upd)

    token = create_token("u1")
    _create_user(fake_supabase, "u1")
    r = client.get(
        "/surveys/available?lang=en&country=JP",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    opt_id = data[0]["choices"][0]["option_id"]

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
    survey, options = _seed_survey(fake_supabase, is_single=False, status="approved")
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

