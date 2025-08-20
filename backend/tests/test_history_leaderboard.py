import os
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.routes.user import router as user_router, get_current_user
from backend.routes.leaderboard import router as leaderboard_router, maybe_user


def make_app(monkeypatch, supa, user_id="u1"):
    app = FastAPI()
    app.include_router(user_router)
    app.include_router(leaderboard_router)
    app.dependency_overrides[get_current_user] = lambda: {"hashed_id": user_id}
    app.dependency_overrides[maybe_user] = lambda: {"hashed_id": user_id}
    monkeypatch.setattr("backend.routes.user.get_supabase_client", lambda: supa)
    monkeypatch.setattr("backend.routes.leaderboard.get_supabase_client", lambda: supa)
    return app


def test_leaderboard_aggregation_and_anonymous(monkeypatch, fake_supabase):
    app = make_app(monkeypatch, fake_supabase)
    supa = fake_supabase
    supa.table("app_users").insert([
        {"hashed_id": "u1", "username": "Alice"},
        {"hashed_id": "u2", "username": ""},
    ]).execute()
    supa.table("user_best_iq").insert(
        [
            {"user_id": "u1", "best_iq": 120},
            {"user_id": "u2", "best_iq": 90},
        ]
    ).execute()
    with TestClient(app) as client:
        resp = client.get("/leaderboard?limit=10")
        payload = resp.json()
        data = payload["items"]
        assert payload["total_users"] == 2
        assert payload["my_rank"] == 1
        assert data[0]["display_name"] == "Alice"
        assert data[0]["best_iq"] == 120
        assert data[1]["display_name"] == f"Guest-{'u2'[:4]}"
        assert data[1]["best_iq"] == 90


def test_history_descending(monkeypatch, fake_supabase):
    user_id = "u1"
    app = make_app(monkeypatch, fake_supabase, user_id)
    supa = fake_supabase
    supa.table("quiz_attempts").insert([
        {"user_id": user_id, "created_at": "2025-01-01T00:00:00Z", "set_id": "A", "iq_score": 100, "percentile": 50, "duration": 30, "status": "submitted"},
        {"user_id": user_id, "created_at": "2025-02-01T00:00:00Z", "set_id": "B", "iq_score": 110, "percentile": 60, "duration": 20, "status": "submitted"},
    ]).execute()
    with TestClient(app) as client:
        resp = client.get("/user/history")
        attempts = resp.json()["attempts"]
        assert [a["set"] for a in attempts] == ["B", "A"]
