import importlib

from backend.services import db_read


def reload_db_read(monkeypatch, use_v2: bool):
    if use_v2:
        monkeypatch.setenv("USE_V2_STATS", "true")
    else:
        monkeypatch.delenv("USE_V2_STATS", raising=False)
    importlib.reload(db_read)


def test_get_user_best_iq(monkeypatch, fake_supabase):
    fake_supabase.tables.setdefault("user_best_iq", []).append({"user_id": "u1", "best_iq": 100})
    fake_supabase.tables.setdefault("user_best_iq_v2", []).append({"user_id": "u1", "best_iq": 150})

    reload_db_read(monkeypatch, False)
    res = db_read.get_user_best_iq("u1")
    assert res and res.best_iq == 100

    reload_db_read(monkeypatch, True)
    res = db_read.get_user_best_iq("u1")
    assert res and res.best_iq == 150


def test_get_survey_choice_iq_stats(monkeypatch, fake_supabase):
    fake_supabase.tables.setdefault("survey_choice_iq_stats", []).append(
        {
            "group_id": "g1",
            "survey_id": "s1",
            "survey_item_id": "i1",
            "responses_count": 2,
            "avg_iq": 100,
        }
    )
    fake_supabase.tables.setdefault("survey_choice_iq_stats_v2", []).append(
        {
            "group_id": "g1",
            "survey_id": "s1",
            "survey_item_id": "i1",
            "responses_count": 3,
            "avg_iq": 120,
        }
    )

    reload_db_read(monkeypatch, False)
    rows = db_read.get_survey_choice_iq_stats(survey_id="s1")
    assert rows[0].responses_count == 2

    reload_db_read(monkeypatch, True)
    rows = db_read.get_survey_choice_iq_stats(survey_id="s1")
    assert rows[0].responses_count == 3
