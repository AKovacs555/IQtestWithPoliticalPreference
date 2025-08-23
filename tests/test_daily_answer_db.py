import os
import sys

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))

from datetime import datetime
from backend import db


class DummyResponse:
    def __init__(self, data=None):
        self.data = data
        self.error = None


class DummyTable:
    def __init__(self, rows, name):
        self.rows = rows
        self.name = name
        self._filters = []
        self._select = False
        self._single = False

    def select(self, *columns):
        self._select = True
        return self

    def insert(self, data):
        if isinstance(data, list):
            for row in data:
                self._insert_row(row)
        else:
            self._insert_row(data)
        return self

    def _insert_row(self, row):
        if self.name == "survey_answers" and "answered_on" not in row:
            created = row.get("created_at") or datetime.utcnow().isoformat() + "Z"
            row["answered_on"] = created[:10]
        self.rows.append(row)

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._select:
            res = [r for r in self.rows if all(r.get(c) == v for c, v in self._filters)]
            result = res[0] if self._single and res else res
            self._reset()
            return DummyResponse(result)
        self._reset()
        return DummyResponse(None)

    def _reset(self):
        self._filters = []
        self._select = False
        self._single = False


class DummySupabase:
    def __init__(self):
        self.tables = {
            "app_users": [],
            "survey_answers": [],
            "survey_items": [],
            "surveys": [],
        }

    def table(self, name):
        if name not in self.tables:
            self.tables[name] = []
        return DummyTable(self.tables[name], name)


def test_insert_and_count(monkeypatch):
    supa = DummySupabase()
    monkeypatch.setattr(db, "get_supabase", lambda: supa, raising=False)

    fixed_now = datetime(2023, 1, 1, 12, 0, 0)
    class FakeDateTime(datetime):
        @classmethod
        def utcnow(cls):
            return fixed_now

        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(db, "datetime", FakeDateTime, raising=False)

    # existing user with UUID
    supa.table("app_users").insert({"id": "uuid1", "hashed_id": "u1"}).execute()

    # populate survey and item mappings
    for i in range(3):
        survey_id = f"s{i}"
        group_id = f"g{i}"
        supa.table("surveys").insert({"id": survey_id, "group_id": group_id}).execute()
        supa.table("survey_items").insert({"id": f"q{i}", "survey_id": survey_id}).execute()

    for i in range(3):
        db.insert_daily_answer("u1", f"q{i}")

    assert all(row["user_id"] == "uuid1" for row in supa.tables["survey_answers"])
    assert db.get_daily_answer_count("u1") == 3
