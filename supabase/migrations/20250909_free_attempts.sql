-- Add free_attempts column and migrate legacy free_tests if present
alter table app_users add column if not exists free_attempts int not null default 0;

-- Rename legacy column if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'app_users' AND column_name = 'free_tests'
    ) THEN
        ALTER TABLE app_users RENAME COLUMN free_tests TO free_attempts;
    END IF;
END $$;

-- Index for quick lookup by id and remaining attempts
create index if not exists app_users_id_free_attempts_idx on app_users(id, free_attempts);
