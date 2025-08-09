-- App users: ensure baseline columns exist
alter table app_users add column if not exists free_credits int not null default 1;
alter table app_users add column if not exists free_credits_used int not null default 0;
alter table app_users add column if not exists referral_code text unique;
alter table app_users add column if not exists referred_by text;

-- Attempts (IQ test sessions)
create table if not exists attempts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null check (status in ('active','completed','timed_out','abandoned')),
  score int,
  constraint fk_attempts_user foreign key (user_id) references auth.users(id)
);

-- Highest IQ ranking view
create view if not exists user_best_iq as
  select user_id, max(score) as best_score
  from attempts
  where score is not null
  group by user_id;

-- Surveys: daily-3 feature (store responses and per-day locks)
create table if not exists survey_responses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  question_id bigint not null,
  answer_index int not null,
  responded_at timestamptz not null default now(),
  constraint uq_user_q unique (user_id, question_id)
);

create table if not exists daily3_locks (
  user_id uuid primary key,
  day date not null,
  count int not null default 0,
  updated_at timestamptz not null default now()
);

-- Subscriptions (Pro Pass)
create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  plan text not null check (plan in ('pro-monthly','pro-yearly')),
  active boolean not null default false,
  current_period_start timestamptz,
  current_period_end timestamptz,
  constraint fk_sub_user foreign key (user_id) references auth.users(id)
);

-- Paid survey submissions (sponsored surveys)
create table if not exists sponsored_surveys (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  title text not null,
  description text,
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  price_yen int not null,
  created_at timestamptz not null default now(),
  approved_at timestamptz,
  constraint fk_ss_user foreign key (user_id) references auth.users(id)
);

-- Price rules (JPY base by country)
create table if not exists price_rules (
  id bigserial primary key,
  country_code text not null,
  kind text not null check (kind in ('pro-monthly','pro-yearly','retry','sponsored')),
  amount_yen int not null
);

-- Referrals (credit +1 for inviter after invitee completes first IQ test)
create table if not exists referrals (
  id uuid primary key default gen_random_uuid(),
  inviter_code text not null,
  invitee_user uuid not null unique,
  credited boolean not null default false,
  credited_at timestamptz
);
