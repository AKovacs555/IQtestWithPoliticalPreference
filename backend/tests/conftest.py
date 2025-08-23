import pytest
import os
import uuid
from datetime import datetime

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
        self._or_filters = []

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
        self._filters.append(("eq", column, value))
        return self

    def _process_row(self, row):
        if self.name == "survey_answers" and "answered_on" not in row:
            created = row.get("created_at") or datetime.utcnow().isoformat() + "Z"
            row["answered_on"] = created[:10]
        return row

    def or_(self, expression):
        """Support simple OR conditions like ``"a.eq.1,b.eq.2"``."""
        parts = []
        for cond in expression.split(","):
            try:
                column, op, value = cond.split(".", 2)
            except ValueError:
                continue
            parts.append((op, column, value))
        if parts:
            self._or_filters.append(parts)
        return self

    def contains(self, column, value):
        """Naive array containment check used in tests."""
        self._filters.append(("contains", column, tuple(value)))
        return self

    def in_(self, column, values):
        self._filters.append(("in", column, tuple(values)))
        return self

    def limit(self, n):
        self._limit = n
        return self

    def order(self, column, desc=False):
        self._order = (column, desc)
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        def _matches(row):
            for op, col, val in self._filters:
                field = row.get(col)
                if op == "eq" and field != val:
                    return False
                if op == "contains":
                    if not isinstance(field, list) or val[0] not in field:
                        return False
                if op == "in" and field not in val:
                    return False
            for group in self._or_filters:
                if not any(row.get(col) == value for op, col, value in group if op == "eq"):
                    return False
            return True

        if getattr(self, '_insert', None) is not None:
            data = self._insert
            if isinstance(data, list):
                processed = [self._process_row(r) for r in data]
                self.rows.extend(processed)
                result = processed
            else:
                processed = self._process_row(data)
                self.rows.append(processed)
                result = processed if self._single else [processed]
            self._reset()
            return DummyResponse(result)
        if getattr(self, '_delete', False):
            self.rows[:] = [r for r in self.rows if not _matches(r)]
            self._reset()
            return DummyResponse(None)
        if getattr(self, '_update', None) is not None:
            for r in self.rows:
                if _matches(r):
                    r.update(self._update)
            self._reset()
            return DummyResponse(None)
        if self._select:
            res = [r for r in self.rows if _matches(r)]
            if getattr(self, '_order', None) and isinstance(res, list):
                col, desc = self._order
                res = sorted(res, key=lambda x: x.get(col), reverse=desc)
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
        self._single = False
        self._limit = None
        self._order = None
        self._or_filters = []

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
    monkeypatch.setattr("backend.routes.stats.get_supabase", lambda: supa, raising=False)
    return supa
