import os, sys
from pathlib import Path
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.main import app, USERS

client = TestClient(app)

def test_ad_flow():
    user_id = 'u1'
    r = client.post('/ads/start', json={'user_id': user_id})
    assert r.status_code == 200
    assert r.json()['status'] == 'started'
    r = client.post('/ads/complete', json={'user_id': user_id})
    assert r.status_code == 200
    assert r.json()['points'] == USERS[user_id]['points']

    r = client.get(f'/points/{user_id}')
    assert r.status_code == 200
    assert r.json()['points'] == USERS[user_id]['points']


def test_pricing_variant():
    user_id = 'variant_user'
    r = client.get(f'/pricing/{user_id}')
    assert r.status_code == 200
    data = r.json()
    assert 'variant' in data
    assert data['price'] in [480, 720, 980]


def test_question_validation():
    tmp = Path('questions/bad.json')
    tmp.write_text('{"id": "bad", "language": "en", "title": "Bad", "questions": [{"id": 0}]}')
    try:
        r = client.get('/quiz/start?set_id=bad')
        assert r.status_code == 400
    finally:
        tmp.unlink()

