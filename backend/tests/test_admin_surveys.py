from fastapi.testclient import TestClient
import os
import sys

# Adjust path so "main" can be imported when tests run from repository root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from main import app
import pytest
from backend.deps.auth import create_token
from backend import db


@pytest.mark.skip("admin setup not configured")
def test_languages_endpoint(monkeypatch):
    token = create_token("u1", is_admin=True)
    monkeypatch.setattr(db, "get_user", lambda _id: {"hashed_id": "u1", "is_admin": True})
    with TestClient(app) as client:
        r = client.get("/admin/surveys/languages", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert "languages" in data
        assert set(["ja", "en", "tr", "ru", "zh", "ko", "es", "fr", "it", "de", "ar"]).issubset(set(data.get("languages", [])))

