ALTER TABLE app_users
  ADD COLUMN IF NOT EXISTS username TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS survey_completed BOOLEAN NOT NULL DEFAULT FALSE;

-- Populate missing usernames with the user's id to ensure uniqueness
UPDATE app_users
  SET username = id::text
WHERE username IS NULL;
