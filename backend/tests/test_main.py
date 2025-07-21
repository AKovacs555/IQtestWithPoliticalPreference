from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.main import app

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
