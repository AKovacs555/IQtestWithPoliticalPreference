import os, sys, asyncio, uuid
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import main
from main import app, AsyncSessionLocal, User


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


def test_verify_otp_creates_user(monkeypatch):
    monkeypatch.setattr("main.send_otp", lambda *a, **k: None)
    phone = "+1234567892"
    with TestClient(app) as client:
        r = client.post("/auth/request-otp", json={"phone": phone})
        assert r.status_code == 200
        code = main.OTP_CODES[phone]
        r = client.post("/auth/verify-otp", json={"phone": phone, "code": code})
        assert r.status_code == 200
        user_id = r.json()["id"]
    async def get_user():
        async with AsyncSessionLocal() as session:
            return await session.get(User, user_id)
    user = asyncio.get_event_loop().run_until_complete(get_user())
    assert user is not None
    assert user.created_at is not None
