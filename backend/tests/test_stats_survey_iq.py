import os
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.routes.stats import router as stats_router


def test_survey_iq_by_option(fake_supabase):
    app = FastAPI()
    app.include_router(stats_router)
    supa = fake_supabase
    supa.table("surveys").insert({"id": "s1", "title": "S1"}).execute()
    supa.table("survey_items").insert([
        {"id": "i1", "survey_id": "s1", "position": 0, "body": "A"},
        {"id": "i2", "survey_id": "s1", "position": 1, "body": "B"},
    ]).execute()
    supa.table("user_best_iq").insert([
        {"user_id": "u1", "best_iq": 100},
        {"user_id": "u2", "best_iq": 80},
    ]).execute()
    supa.table("survey_answers").insert([
        {"user_id": "u1", "survey_id": "s1", "survey_item_id": "i1"},
        {"user_id": "u2", "survey_id": "s1", "survey_item_id": "i1"},
        {"user_id": "u2", "survey_id": "s1", "survey_item_id": "i2"},
    ]).execute()

    with TestClient(app) as client:
        resp = client.get("/stats/surveys/s1/iq_by_option")
        assert resp.status_code == 200
        data = resp.json()
        assert data["survey_id"] == "s1"
        items = {i["option_index"]: i for i in data["items"]}
        assert items[0]["count"] == 2
        assert abs(items[0]["avg_iq"] - 90.0) < 0.01
        assert items[1]["count"] == 1
        assert items[1]["avg_iq"] == 80
