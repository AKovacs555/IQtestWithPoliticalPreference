import os
import sys
import asyncio
import pytest

sys.path.insert(0, os.path.abspath("."))
from backend.routes.admin_questions import approve_all, ApproveAllRequest


class FakeQuery:
    def __init__(self, with_count=False):
        self.with_count = with_count
        self.ops = []

    def select(self, *args, **kwargs):
        self.ops.append("select")
        return self

    def update(self, data):
        self.ops.append("update")
        return self

    def eq(self, *args, **kwargs):
        self.ops.append("eq")
        return self

    def is_(self, *args, **kwargs):
        self.ops.append("is")
        return self

    def execute(self):
        self.ops.append("execute")

        class Resp:
            def __init__(self, count):
                self.data = []
                self.count = count

        return Resp(1 if self.with_count else 0)


class FakeSupabase:
    def __init__(self):
        self.builders = []

    def table(self, name):
        q = FakeQuery(with_count=len(self.builders) == 0)
        self.builders.append(q)
        return q


@pytest.mark.smoke
def test_approve_all_update_order(monkeypatch):
    fake = FakeSupabase()
    monkeypatch.setattr(
        "backend.routes.admin_questions.get_supabase_client", lambda: fake
    )
    payload = ApproveAllRequest(approved=True, lang="ja", only_delta=True)
    result = asyncio.run(approve_all(payload))
    assert result["approved"] is True
    assert result["updated"] >= 0
    ops = fake.builders[1].ops
    assert ops[0] == "update"
    assert "execute" in ops
