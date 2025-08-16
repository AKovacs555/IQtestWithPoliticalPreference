import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from main import app


def test_arena_iq_stats_scopes(fake_supabase):
    client = TestClient(app)
    supa = fake_supabase
    supa.tables.setdefault("survey_group_choice_iq_stats", []).append(
        {
            "group_id": "g1",
            "survey_id": "s1",
            "survey_item_id": "o1",
            "responses_count": 5,
            "avg_iq": 100,
        }
    )
    supa.tables.setdefault("survey_choice_iq_stats", []).extend(
        [
            {
                "group_id": "g1",
                "survey_id": "s1",
                "survey_item_id": "o1",
                "responses_count": 2,
                "avg_iq": 100,
            },
            {
                "group_id": "g1",
                "survey_id": "s1",
                "survey_item_id": "o2",
                "responses_count": 3,
                "avg_iq": 120,
            },
        ]
    )

    r = client.get("/arena/iq_stats")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get("/arena/iq_stats", params={"scope": "item"})
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get("/arena/iq_stats", params={"scope": "survey"})
    assert r.status_code == 200
    data = r.json()
    assert data[0]["survey_id"] == "s1"
    assert data[0]["responses_count"] == 5
    assert abs(data[0]["avg_iq"] - 112.0) < 0.01
