-- Adds a `points` column to the `app_users` table if it doesn't already exist.
alter table public.app_users
  add column if not exists points integer not null default 0;

-- Ensure existing rows have non-null points
update public.app_users
  set points = 0
where points is null;
