import os
import sys
import uuid
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app  # noqa
from backend import db  # noqa


def test_survey_submit_persists_answers_and_marks_completion():
    uid = str(uuid.uuid4())
    db.create_user({
        'id': uid,
        'hashed_id': uid,
        'plays': 0,
        'referrals': 0,
        'points': 0,
        'scores': [],
        'party_log': [],
        'demographic': {},
        'demographic_completed': False,
        'survey_completed': False,
    })

    survey_id = str(uuid.uuid4())
    group_id = str(uuid.uuid4())
    item_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

    supa = db.get_supabase()
    supa.table('survey_items').insert([
        {'id': item_ids[0], 'survey_id': survey_id, 'position': 0},
        {'id': item_ids[1], 'survey_id': survey_id, 'position': 1},
    ]).execute()

    payload = {
        'user_id': uid,
        'lang': 'en',
        'survey_id': survey_id,
        'survey_group_id': group_id,
        'answers': [{'id': survey_id, 'selections': [1]}],
    }

    with TestClient(app) as client:
        r = client.post('/survey/submit', json=payload)
        assert r.status_code == 200

    user = db.get_user(uid)
    assert user['survey_completed'] is True

    answers = supa.tables.get('survey_answers', [])
    assert len(answers) == 1
    row = answers[0]
    assert row['survey_item_id'] == item_ids[1]
    assert row['survey_id'] == survey_id
    assert row['survey_group_id'] == group_id
    assert row['user_id'] == uid
