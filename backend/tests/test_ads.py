import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from main import app
from backend import db
from backend.deps.auth import create_token


def test_ad_flow():
    user_id = 'u1'
    with TestClient(app) as client:
        r = client.post('/ads/start', json={'user_id': user_id})
        assert r.status_code == 200
        assert r.json()['status'] == 'started'
        r = client.post('/ads/complete', json={'user_id': user_id})
        assert r.status_code == 200
        points = r.json()['points']

        r = client.get(f'/points/{user_id}')
        assert r.status_code == 200
        assert r.json()['points'] == points


def test_pricing_variant():
    user_id = 'variant_user'
    with TestClient(app) as client:
        r = client.get(f'/pricing/{user_id}')
        assert r.status_code == 200
        data = r.json()
        assert 'retry' in data and 'pro_pass' in data


def test_question_validation():
    tmp = Path(__file__).resolve().parent.parent / 'questions' / 'bad.json'
    tmp.write_text('{"id": "bad", "language": "en", "title": "Bad", "questions": [{"id": 0}]}')
    try:
        user_id = 'testuser'
        db.create_user({'hashed_id': user_id, 'nationality': 'US', 'survey_completed': True, 'demographic_completed': True})
        token = create_token(user_id)
        with TestClient(app) as client:
            r = client.get('/quiz/start?set_id=bad', headers={"Authorization": f"Bearer {token}"})
            assert r.status_code == 404
    finally:
        tmp.unlink()

