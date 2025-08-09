import os, sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app
from backend import db


def _create_user(uid):
    data = {
        'hashed_id': uid,
        'salt': '',
        'plays': 0,
        'referrals': 0,
        'points': 0,
        'scores': [],
        'party_log': [],
        'demographic': {},
        'demographic_completed': False,
        'free_attempts': 0,
        'survey_completed': False,
    }
    return db.create_user(data)['id']


def test_survey_submit_handles_null_lr_auth(monkeypatch):
    surveys = [
        {
            "id": 1,
            "statement": "q",
            "options": ["a", "b"],
            "type": "sa",
            "exclusive_options": [],
            "lr": None,
            "auth": None,
        }
    ]
    monkeypatch.setattr('main.get_surveys', lambda lang=None: surveys)
    with TestClient(app) as client:
        r = client.post('/survey/submit', json={"answers": [{"id": "1", "selections": [0]}]})
        assert r.status_code == 200
        data = r.json()
        assert data["left_right"] == 0
        assert data["libertarian_authoritarian"] == 0


def test_survey_submit_persists_answers_and_marks_completion(monkeypatch):
    uid = 'user10'
    user_uuid = _create_user(uid)
    surveys = [
        {
            "id": 1,
            "group_id": 'g1',
            "statement": "q",
            "options": ["a", "b"],
            "type": "sa",
            "exclusive_options": [],
            "lr": 0,
            "auth": 0,
        }
    ]
    monkeypatch.setattr('main.get_surveys', lambda lang=None: surveys)
    payload = {"answers": [{"id": "1", "selections": [0]}], "user_id": uid}
    with TestClient(app) as client:
        r = client.post('/survey/submit', json=payload)
        assert r.status_code == 200

    # user should be flagged as completed
    user = db.get_user(uid)
    assert user['survey_completed'] is True

    # survey response should be persisted with expected fields
    supa = db.get_supabase()
    assert len(supa.tables.get('survey_responses', [])) == 1
    assert supa.tables['survey_responses'][0] == {
        'user_id': user_uuid,
        'survey_id': '1',
        'survey_group_id': 'g1',
        'answer': {"id": "1", "selections": [0]},
    }
