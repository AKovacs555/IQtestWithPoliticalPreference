from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from main import app

def test_ping():
    with TestClient(app) as client:
        r = client.get('/ping')
        assert r.status_code == 200
        assert r.json() == {"message": "pong"}


def test_analytics_endpoint():
    with TestClient(app) as client:
        r = client.post('/analytics', json={'event': 'test'})
        assert r.status_code == 200
        assert r.json() == {}


def test_dif_report_auth():
    with TestClient(app) as client:
        r = client.get('/admin/dif-report?api_key=bad')
        assert r.status_code == 403


def test_upload_questions_auth():
    os.environ["ADMIN_API_KEY"] = "secret"
    with TestClient(app) as client:
        r = client.post(
            "/admin/upload-questions",
            json={"questions": []},
            headers={"X-Admin-Api-Key": "bad"},
        )
        assert r.status_code == 401


def test_upload_questions_success(monkeypatch):
    os.environ["ADMIN_API_KEY"] = "secret"

    stored = {}
    from pathlib import Path

    orig_read = Path.read_text
    orig_write = Path.write_text

    def fake_read(self, *args, **kwargs):
        if self.name == "question_bank.json":
            return stored.get("data", "[]")
        return orig_read(self, *args, **kwargs)

    def fake_write(self, data, *args, **kwargs):
        if self.name == "question_bank.json":
            stored["data"] = data
            return len(data)
        return orig_write(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read)
    monkeypatch.setattr(Path, "write_text", fake_write)

    item = {
        "id": 0,
        "question": "1+1?",
        "options": ["1", "2", "3", "4"],
        "answer": 1,
        "irt": {"a": 1.0, "b": 0.0}
    }

    with TestClient(app) as client:
        r = client.post(
            "/admin/upload-questions",
            json={"questions": [item]},
            headers={"X-Admin-Api-Key": "secret"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert "Imported" in data.get("log", "")

def test_history_sorted():
    from backend import db
    user_id = 'hist_user'
    db.create_user({
        'hashed_id': user_id,
        'salt': '',
        'plays': 0,
        'referrals': 0,
        'points': 0,
        'scores': [
            {
                'iq': 100,
                'percentile': 50,
                'timestamp': '2023-01-01T00:00:00',
                'set_id': 'set1'
            },
            {
                'iq': 110,
                'percentile': 75,
                'timestamp': '2023-02-01T00:00:00',
                'set_id': 'set2'
            }
        ],
        'party_log': [],
        'demographic': {}
    })
    with TestClient(app) as client:
        r = client.get(f'/user/history/{user_id}')
        assert r.status_code == 200
        data = r.json()
        assert len(data['scores']) == 2
        assert data['scores'][0]['timestamp'] == '2023-02-01T00:00:00'
        assert data['scores'][1]['timestamp'] == '2023-01-01T00:00:00'
