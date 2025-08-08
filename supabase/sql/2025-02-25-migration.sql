-- 1) Daily progress (owner-only RLS)
create table if not exists public.survey_daily_progress(
  user_id text not null references public.users(hashed_id) on delete cascade,
  ymd date not null,
  answered_count int not null default 0,
  last_served_ids int[] not null default '{}',
  primary key(user_id, ymd)
);
alter table public.survey_daily_progress enable row level security;
create policy "own daily progress" on public.survey_daily_progress
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- 2) Quiz sessions (owner-only)
create table if not exists public.quiz_sessions(
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.users(hashed_id) on delete cascade,
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  status text not null default 'active' check (status in ('active','submitted','abandoned','timeout')),
  fingerprint text
);
alter table public.quiz_sessions enable row level security;
create policy "own sessions" on public.quiz_sessions
  for all to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());

-- 3) Pro pass & pricing rules
alter table public.users add column if not exists pro_active_until timestamptz;
create table if not exists public.pricing_rules(
  region text primary key,
  jpy_monthly int not null,
  jpy_yearly int not null,
  jpy_retry_tiers int[] not null default '{480,720,980}'
);

-- 4) Referral rewards idempotency
create table if not exists public.referral_rewards(
  referrer_id text not null references public.users(hashed_id) on delete cascade,
  referred_id text not null references public.users(hashed_id) on delete cascade,
  rewarded_at timestamptz not null default now(),
  primary key(referrer_id, referred_id)
);
