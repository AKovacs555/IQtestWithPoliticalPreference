ALTER TABLE questions ADD COLUMN IF NOT EXISTS approved boolean NOT NULL DEFAULT false;
