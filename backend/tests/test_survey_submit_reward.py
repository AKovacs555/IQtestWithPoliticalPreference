import os
import sys
import uuid
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app  # noqa
from backend import db  # noqa


def test_survey_submit_grants_daily_points():
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

    supa = db.get_supabase()

    with TestClient(app) as client:
        for _ in range(3):
            survey_id = str(uuid.uuid4())
            group_id = str(uuid.uuid4())
            item_id = str(uuid.uuid4())
            supa.table('survey_items').insert({
                'id': item_id,
                'survey_id': survey_id,
                'position': 0,
            }).execute()
            payload = {
                'user_id': uid,
                'lang': 'en',
                'survey_id': survey_id,
                'survey_group_id': group_id,
                'answers': [{'id': survey_id, 'selections': [0]}],
            }
            res = client.post('/survey/submit', json=payload)
            assert res.status_code == 200

    ledger = supa.tables.get('point_ledger', [])
    entries = [r for r in ledger if r['user_id'] == uid and r['reason'] == 'daily3']
    assert len(entries) == 1
