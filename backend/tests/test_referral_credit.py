from types import SimpleNamespace

import backend.referral as ref

class DummyTable:
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.filters = []
        self._update = None
        self.single_flag = False
    def select(self, *_):
        return self
    def eq(self, field, value):
        self.filters.append((field, value))
        return self
    def single(self):
        self.single_flag = True
        return self
    def update(self, data):
        self._update = data
        return self
    def execute(self):
        if self.name == 'referrals':
            rows = [r for r in self.db.referrals if all(r.get(f) == v for f, v in self.filters)]
            if self._update is not None:
                for r in rows:
                    r.update(self._update)
            data = rows[0] if self.single_flag else rows
            return SimpleNamespace(data=data)
        elif self.name == 'app_users':
            rows = [u for u in self.db.app_users.values() if all(u.get(f) == v for f, v in self.filters)]
            if self._update is not None:
                for u in rows:
                    u.update(self._update)
            data = rows[0] if self.single_flag else rows
            return SimpleNamespace(data=data)
        return SimpleNamespace(data=None)

class DummySupabase:
    def __init__(self):
        self.app_users = {
            'inviter': {'hashed_id': 'inviter', 'invite_code': 'ABC123', 'free_attempts': 0},
            'invitee': {'hashed_id': 'invitee'}
        }
        self.referrals = [
            {'inviter_code': 'ABC123', 'invitee_user': 'invitee', 'credited': False}
        ]
    def table(self, name):
        return DummyTable(self, name)


def test_referrer_credit(monkeypatch):
    db = DummySupabase()
    monkeypatch.setenv('REFERRAL_MAX_CREDITS', '3')
    monkeypatch.setattr(ref, 'get_supabase_client', lambda: db)
    ref.credit_referral_if_applicable('invitee')
    assert db.app_users['inviter']['free_attempts'] == 1
    assert db.referrals[0]['credited'] is True
