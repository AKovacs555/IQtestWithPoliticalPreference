import os
from fastapi.testclient import TestClient
import sys

# Adjust path so "main" can be imported when tests run from repository root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from main import app


def test_languages_endpoint():
    os.environ["ADMIN_API_KEY"] = "secret"
    with TestClient(app) as client:
        r = client.get("/admin/surveys/languages", headers={"X-Admin-Api-Key": "secret"})
        assert r.status_code == 200
        data = r.json()
        assert "languages" in data
        assert set(["ja", "en", "tr", "ru", "zh", "ko", "es", "fr", "it", "de", "ar"]).issubset(set(data["languages"]))

