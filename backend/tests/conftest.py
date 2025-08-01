import pytest

class DummyResponse:
    def __init__(self, data=None):
        self.data = data
        self.error = None

class DummyTable:
    def __init__(self, rows):
        self.rows = rows
        self._select = False
        self._insert = None
        self._update = None
        self._eq_column = None
        self._eq_value = None
        self._single = False
        self._limit = None

    def select(self, *_):
        self._select = True
        return self

    def insert(self, data):
        self._insert = data
        return self

    def update(self, data):
        self._update = data
        return self

    def eq(self, column, value):
        self._eq_column = column
        self._eq_value = value
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
                return DummyResponse(self._insert)
            else:
                self.rows.append(self._insert)
                return DummyResponse([self._insert])
        if self._update is not None:
            for r in self.rows:
                if r.get(self._eq_column) == self._eq_value:
                    r.update(self._update)
            return DummyResponse(None)
        if self._select:
            res = [r for r in self.rows if r.get(self._eq_column) == self._eq_value] if self._eq_column else self.rows
            if self._single:
                res = res[0] if res else None
            if self._limit is not None and isinstance(res, list):
                res = res[: self._limit]
            return DummyResponse(res)
        return DummyResponse(None)

class DummySupabase:
    def __init__(self):
        self.users = []

    def from_(self, table):
        assert table == "users"
        return DummyTable(self.users)

@pytest.fixture(autouse=True)
def fake_supabase(monkeypatch):
    supa = DummySupabase()
    monkeypatch.setattr("db.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("backend.db.get_supabase", lambda: supa, raising=False)
    monkeypatch.setattr("main.get_supabase", lambda: supa, raising=False)
    return supa
