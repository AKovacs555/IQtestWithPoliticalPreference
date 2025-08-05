from fastapi.testclient import TestClient
from backend.main import app


def test_register_and_login(fake_supabase):
    with TestClient(app) as client:
        payload = {"username": "user1", "email": "user@example.com", "password": "secret"}
        r = client.post("/auth/register", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data.get("user_id")
        assert len(fake_supabase.tables["users"]) == 1
        r2 = client.post("/auth/login", json={"identifier": "user@example.com", "password": "secret"})
        assert r2.status_code == 200
        assert r2.json()["user_id"] == data["user_id"]
