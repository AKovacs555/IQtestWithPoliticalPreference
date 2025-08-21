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

