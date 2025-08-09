-- Add or rename free attempt counter column
alter table public.users
    rename column if exists free_tests to free_attempts;

alter table public.users
    add column if not exists free_attempts integer not null default 0;

create index if not exists idx_users_id_free_attempts
    on public.users (id, free_attempts);
