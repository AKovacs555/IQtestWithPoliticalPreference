import os, sys, uuid
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import main
from main import app
from backend import db


def test_payment_flow(monkeypatch):
    user_id = f"pay_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr("main.AD_REWARD_POINTS", 5)
    monkeypatch.setattr("main.RETRY_POINT_COST", 5)
    with TestClient(app) as client:
        r = client.post("/play/record", json={"user_id": user_id})
        assert r.status_code == 200
        assert r.json()["plays"] == 1
        r = client.post("/play/record", json={"user_id": user_id})
        assert r.status_code == 402
        client.post("/ads/complete", json={"user_id": user_id})
        r = client.post("/play/record", json={"user_id": user_id})
        assert r.status_code == 200
        assert r.json()["plays"] == 2
