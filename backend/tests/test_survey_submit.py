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
        'free_attempts': 0,
        'survey_completed': False,
    }
    db.create_user(data)


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


def test_survey_submit_marks_completion(monkeypatch):
    uid = 'user10'
    _create_user(uid)
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
    with TestClient(app) as client:
        r = client.post('/survey/submit', json={"answers": [{"id": "1", "selections": [0]}], "user_id": uid})
        assert r.status_code == 200
    user = db.get_user(uid)
    assert user['survey_completed'] is True
    supa = db.get_supabase()
    assert supa.tables['survey_responses'][0]['user_id'] == uid
