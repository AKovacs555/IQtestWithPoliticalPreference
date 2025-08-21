from backend.db import upsert_user


def test_upsert_user_assigns_random_username(fake_supabase):
    user_id = "u1"
    email = "u1@example.com"
    upsert_user(user_id, email=email)
    users = fake_supabase.tables["app_users"]
    assert users[0]["email"] == email
    first_username = users[0]["username"]
    assert first_username and first_username != email

    users[0]["username"] = "bad@name"
    upsert_user(user_id, email=email)
    second_username = users[0]["username"]
    assert second_username and second_username != "bad@name"
    assert second_username != first_username


def test_upsert_user_retries_on_duplicate(monkeypatch, fake_supabase):
    import backend.db as db

    fake_supabase.table("app_users").insert(
        {"id": "e1", "hashed_id": "e1", "username": "Silly Donkey"}
    ).execute()

    names = iter(["Silly Donkey", "Silly Donkey", "Chilly Ferret"])
    monkeypatch.setattr(db, "_random_username", lambda: next(names))

    upsert_user("u2")
    users = [r for r in fake_supabase.tables["app_users"] if r["id"] == "u2"]
    assert users and users[0]["username"] == "Chilly Ferret"

