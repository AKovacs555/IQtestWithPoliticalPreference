ALTER TABLE users
  ADD COLUMN IF NOT EXISTS free_attempts integer NOT NULL DEFAULT 1;
UPDATE users SET free_attempts = 1 WHERE free_attempts IS NULL;
