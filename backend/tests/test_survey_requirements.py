import os, sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app
from backend import db
import routes.quiz as quiz


def _create_user(uid, extra=None):
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
    if extra:
        data.update(extra)
    db.create_user(data)


def test_quiz_requires_survey_completion(monkeypatch):
    uid = 'user1'
    _create_user(uid)
    monkeypatch.setattr(
        quiz,
        'get_balanced_random_questions_by_set',
        lambda n, sid: [{'id': 1, 'question': 'q', 'options': ['a'], 'answer': 0}],
    )
    with TestClient(app) as client:
        r = client.get(f'/quiz/start?set_id=set1&user_id={uid}')
        assert r.status_code == 400
        assert r.json()['detail']['error'] == 'survey_required'
        db.update_user(uid, {'survey_completed': True})
        r = client.get(f'/quiz/start?set_id=set1&user_id={uid}')
        assert r.status_code == 200
        assert 'questions' in r.json()


def test_survey_complete_endpoint():
    uid = 'user2'
    _create_user(uid)
    with TestClient(app) as client:
        r = client.post('/survey/complete', json={'user_id': uid})
        assert r.status_code == 200
        assert r.json()['status'] == 'ok'
    user = db.get_user(uid)
    assert user['survey_completed'] is True


def test_survey_start_filters_nationality(monkeypatch):
    uid = 'user3'
    _create_user(uid, {'nationality': 'US'})
    surveys = [
        {'id': 1, 'statement': 'us', 'options': [], 'type': 'sa', 'exclusive_options': [], 'target_countries': ['US']},
        {'id': 2, 'statement': 'jp', 'options': [], 'type': 'sa', 'exclusive_options': [], 'target_countries': ['JP']},
        {'id': 3, 'statement': 'all', 'options': [], 'type': 'sa', 'exclusive_options': [], 'target_countries': []},
    ]
    monkeypatch.setattr('main.get_surveys', lambda lang: surveys)
    monkeypatch.setattr('main.get_parties', lambda: [])
    with TestClient(app) as client:
        r = client.get(f'/survey/start?user_id={uid}')
        assert r.status_code == 200
        data = r.json()
        ids = {item['id'] for item in data['items']}
        assert ids == {'1', '3'}
