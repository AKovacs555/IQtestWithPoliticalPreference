import os, sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app


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
