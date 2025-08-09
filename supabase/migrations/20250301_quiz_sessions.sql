create table if not exists quiz_sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid,
    status text check (status in ('started','submitted','timeout','abandoned')),
    started_at timestamptz not null default now(),
    expires_at timestamptz not null,
    set_id text,
    score numeric,
    percentile numeric
);
