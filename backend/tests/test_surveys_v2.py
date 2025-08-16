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
from backend.routes.admin_surveys import SUPPORTED_LANGS


def _create_user(supa, uid: str, gender: str | None = None):
    supa.tables.setdefault("app_users", []).append({"hashed_id": uid, "gender": gender})


def _seed_survey(
    supa,
    *,
    lang="en",
    survey_type="sa",
    status="approved",
    target_genders=None,
    group_id="g1",
):
    survey = {
        "id": "s1",
        "title": "t",
        "question_text": "q1",
        "lang": lang,
        "target_countries": ["JP"],
        "target_genders": target_genders or [],
        "type": survey_type,
        "status": status,
        "is_active": True,
        "group_id": group_id,
    }
    supa.tables.setdefault("surveys", []).append(survey)
    items = [
        {
            "id": "o1",
            "survey_id": "s1",
            "statement": "A",
            "position": 1,
            "is_exclusive": False,
            "lang": lang,
        },
        {
            "id": "o2",
            "survey_id": "s1",
            "statement": "Other",
            "position": 2,
            "is_exclusive": False,
            "lang": lang,
        },
    ]
    supa.tables.setdefault("survey_items", []).extend(items)
    return survey, items


def test_item_language_on_create(fake_supabase):
    app.dependency_overrides[require_admin] = lambda: True
    client = TestClient(app)
    payload = {
        "title": "Title",
        "question_text": "What?",
        "type": "sa",
        "lang": "ja",
        "items": [{"body": "A"}, {"body": "B"}],
        "status": "approved",
        "target_countries": ["JP"],
    }
    r = client.post("/admin/surveys", json=payload)
    assert r.status_code == 201
    items = fake_supabase.tables.get("survey_items", [])
    assert len(items) == 2
    assert all(it.get("lang") == "ja" for it in items)


def test_translation_fanout(fake_supabase, monkeypatch):
    app.dependency_overrides[require_admin] = lambda: True
    monkeypatch.setattr(
        "backend.routes.admin_surveys.translate_with_openai", lambda prompt: "T"
    )
    monkeypatch.setattr(
        "routes.admin_surveys.translate_with_openai", lambda prompt: "T"
    )
    client = TestClient(app)
    payload = {
        "title": "Title",
        "question_text": "What?",
        "type": "sa",
        "lang": "ja",
        "items": [{"body": "A"}, {"body": "B"}],
    }
    r = client.post("/admin/surveys", json=payload)
    assert r.status_code == 201
    surveys = fake_supabase.tables.get("surveys", [])
    group_ids = {s.get("group_id") for s in surveys}
    assert len(surveys) == 1 + len(SUPPORTED_LANGS)
    assert len(group_ids) == 1
    items = fake_supabase.tables.get("survey_items", [])
    for s in surveys:
        s_items = [it for it in items if it.get("survey_id") == s["id"]]
        assert len(s_items) == 2
        assert all(it.get("lang") == s["lang"] for it in s_items)

def test_admin_crud_and_user_flow(fake_supabase):
    app.dependency_overrides[require_admin] = lambda: True
    client = TestClient(app)

    payload = {
        "title": "Title",
        "question_text": "What?",
        "lang": "en",
        "target_countries": ["JP"],
        "type": "sa",
        "target_genders": [],
        "status": "approved",
        "items": [{"body": "Yes"}, {"body": "No"}],
    }
    r = client.post("/admin/surveys", json=payload)
    assert r.status_code == 201
    survey_id = r.json()["id"]

    upd = dict(payload)
    upd["question_text"] = "Updated?"
    upd["items"][0]["body"] = "Sure"
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
    answers = fake_supabase.tables.get("survey_answers", [])
    assert len(answers) == 1
    assert answers[0]["survey_item_id"] == opt_id

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
    survey, options = _seed_survey(fake_supabase, survey_type="ma", status="approved")
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
    answers = fake_supabase.tables.get("survey_answers", [])
    assert len(answers) == len(opt_ids)


def test_gender_filtering(fake_supabase):
    app.dependency_overrides[require_admin] = lambda: True
    client = TestClient(app)

    # create survey targeting male users
    payload = {
        "title": "Gendered",
        "question_text": "Who?",
        "lang": "en",
        "target_countries": ["JP"],
        "target_genders": ["male"],
        "type": "sa",
        "status": "approved",
        "items": [{"body": "Yes"}, {"body": "No"}],
    }
    r = client.post("/admin/surveys", json=payload)
    assert r.status_code == 201

    token_f = create_token("f1")
    _create_user(fake_supabase, "f1", gender="female")
    r = client.get(
        "/surveys/available?lang=en&country=JP",
        headers={"Authorization": f"Bearer {token_f}"},
    )
    assert r.status_code == 200
    assert r.json() == []

    token_m = create_token("m1")
    _create_user(fake_supabase, "m1", gender="male")
    r = client.get(
        "/surveys/available?lang=en&country=JP",
        headers={"Authorization": f"Bearer {token_m}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1

