from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from main import app

client = TestClient(app)

def test_ping():
    r = client.get('/ping')
    assert r.status_code == 200
    assert r.json() == {"message": "pong"}


def test_analytics_endpoint():
    r = client.post('/analytics', json={'event': 'test'})
    assert r.status_code == 200
    assert r.json() == {}


def test_dif_report_auth():
    r = client.get('/admin/dif-report?api_key=bad')
    assert r.status_code == 403


def test_upload_questions_auth():
    os.environ["ADMIN_API_KEY"] = "secret"
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
        "text": "1+1?",
        "options": ["1", "2", "3", "4"],
        "correct_index": 1,
        "category": "数理",
        "difficulty": "easy",
        "irt": {"a": 1.0, "b": 0.0},
    }

    r = client.post(
        "/admin/upload-questions",
        json={"questions": [item]},
        headers={"X-Admin-Api-Key": "secret"},
    )
    assert r.status_code == 200
    assert r.json()["count"] == 1
    assert "1+1?" in stored.get("data", "")
