import pytest
import os
import uuid

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")
os.environ.setdefault("OPENAI_API_KEY", "test")

class DummyResponse:
    def __init__(self, data=None):
        self.data = data
        self.error = None

class DummyTable:
    def __init__(self, rows, name):
        self.rows = rows
        self.name = name
        self._select = False
        self._insert = None
        self._update = None
        self._filters = []
        self._single = False
        self._limit = None

    def select(self, *columns):
        self._select = True
        return self

    def insert(self, data):
        # Auto-generate UUIDs for user rows when missing.
        if self.name == "app_users":
            def ensure_id(row: dict) -> dict:
                row = dict(row)
                row.setdefault("id", str(uuid.uuid4()))
                return row

            if isinstance(data, list):
                data = [ensure_id(r) for r in data]
            else:
                data = ensure_id(data)
        self._insert = data
        return self

    def update(self, data):
        self._update = data
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def limit(self, n):
        self._limit = n
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._insert is not None:
            if isinstance(self._insert, list):
                self.rows.extend(self._insert)
                result = self._insert
            else:
                self.rows.append(self._insert)
                result = [self._insert]
            self._reset()
            return DummyResponse(result)
        if self._update is not None:
            for r in self.rows:
                if all(r.get(col) == val for col, val in self._filters):
                    r.update(self._update)
            self._reset()
            return DummyResponse(None)
        if self._select:
            res = [r for r in self.rows if all(r.get(col) == val for col, val in self._filters)]
            if self._single:
                res = res[0] if res else None
            if self._limit is not None and isinstance(res, list):
                res = res[: self._limit]
            self._reset()
            return DummyResponse(res)
        self._reset()
        return DummyResponse(None)

    def _reset(self):
        self._select = False
        self._insert = None
        self._update = None
        self._filters = []
        self._single = False
        self._limit = None

class DummySupabase:
    def __init__(self):
        self.tables = {"app_users": []}

    def from_(self, table):
        if table not in self.tables:
            self.tables[table] = []
        return DummyTable(self.tables[table], table)

    def table(self, name):
        return self.from_(name)

@pytest.fixture(autouse=True)
def fake_supabase(monkeypatch):
    supa = DummySupabase()
    monkeypatch.setattr("db.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("backend.db.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("main.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("backend.utils.settings.supabase", supa, raising=False)
    monkeypatch.setattr("backend.routes.settings.supabase", supa, raising=False)
    return supa
