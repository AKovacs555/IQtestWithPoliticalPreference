import backend.referral as ref


def test_referrer_credit(monkeypatch, fake_supabase):
    fake_supabase.table("app_users").insert([
        {"hashed_id": "inviter", "invite_code": "ABC123", "free_attempts": 0},
        {"hashed_id": "invitee"},
    ]).execute()
    fake_supabase.table("referrals").insert(
        {"inviter_code": "ABC123", "invitee_user": "invitee", "credited": False}
    ).execute()
    monkeypatch.setenv("REFERRAL_MAX_CREDITS", "3")
    monkeypatch.setattr(ref, "get_supabase_client", lambda: fake_supabase)
    ref.credit_referral_if_applicable("invitee")
    inviter = next(r for r in fake_supabase.tables["app_users"] if r["hashed_id"] == "inviter")
    assert inviter["free_attempts"] == 1
    assert fake_supabase.tables["referrals"][0]["credited"] is True
    ledger = fake_supabase.tables.get("attempt_ledger", [])
    assert ledger[0]["reason"] == "referral"
    assert ledger[0]["delta"] == 1
