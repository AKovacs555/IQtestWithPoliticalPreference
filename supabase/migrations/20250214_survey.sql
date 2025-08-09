-- Survey base and Daily 3 feature tables
create table if not exists surveys (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  lang text not null default 'ja',
  status text not null default 'draft',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists survey_items (
  id uuid primary key default gen_random_uuid(),
  survey_id uuid not null references surveys(id) on delete cascade,
  body text not null,
  choices jsonb not null,
  order_no int not null,
  lang text not null default 'ja',
  is_active boolean not null default true,
  created_at timestamptz default now()
);

create table if not exists survey_responses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  item_id uuid not null references survey_items(id) on delete cascade,
  answer_index int not null,
  answered_on date generated always as (created_at at time zone 'Asia/Tokyo') stored,
  created_at timestamptz not null default now()
);

create unique index if not exists uq_response_one_per_user_item_per_day
  on survey_responses(user_id, item_id, answered_on);

create index if not exists idx_responses_user_day
  on survey_responses(user_id, answered_on);
