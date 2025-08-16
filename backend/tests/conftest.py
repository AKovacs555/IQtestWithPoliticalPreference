import pytest
import os
import uuid

os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "dummy")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test")

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

    def insert(self, data, returning=None):
        """Record rows slated for insertion with automatic ``id`` generation."""

        def ensure_id(row: dict) -> dict:
            row = dict(row)
            row.setdefault("id", str(uuid.uuid4()))
            return row

        if isinstance(data, list):
            data = [ensure_id(r) for r in data]
        else:
            data = ensure_id(data)
        self._insert = data
        self._returning = returning  # ignored but kept for API parity
        return self

    def upsert(self, data, **kwargs):
        """Simplified upsert behaving like insert for tests."""
        return self.insert(data)

    def update(self, data):
        self._update = data
        return self

    def delete(self):
        self._delete = True
        return self

    def eq(self, column, value):
        self._filters.append((column, value))
        return self

    def contains(self, column, value):
        """Naive array containment check used in tests."""
        self._filters.append((column, tuple(value)))
        self._contains = True
        return self

    def limit(self, n):
        self._limit = n
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if getattr(self, '_insert', None) is not None:
            data = self._insert
            if isinstance(data, list):
                self.rows.extend(data)
                result = data
            else:
                self.rows.append(data)
                result = data if self._single else [data]
            self._reset()
            return DummyResponse(result)
        if getattr(self, '_delete', False):
            self.rows[:] = [r for r in self.rows if not all(r.get(c) == v for c, v in self._filters)]
            self._reset()
            return DummyResponse(None)
        if getattr(self, '_update', None) is not None:
            for r in self.rows:
                if all(r.get(col) == val for col, val in self._filters):
                    r.update(self._update)
            self._reset()
            return DummyResponse(None)
        if self._select:
            res = []
            for r in self.rows:
                match = True
                for col, val in self._filters:
                    if getattr(self, '_contains', False) and isinstance(r.get(col), list):
                        if val[0] not in r.get(col, []):
                            match = False
                            break
                    elif r.get(col) != val:
                        match = False
                        break
                if match:
                    res.append(r)
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
        self._delete = False
        self._filters = []
        self._contains = False
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
    monkeypatch.setattr("backend.core.supabase_admin.supabase_admin", supa, raising=False)
    monkeypatch.setattr("main.supabase_admin", supa, raising=False)
    monkeypatch.setattr("backend.routes.admin_surveys.supabase_admin", supa, raising=False)
    monkeypatch.setattr("routes.admin_surveys.supabase_admin", supa, raising=False)
    return supa
