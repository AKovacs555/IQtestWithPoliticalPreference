alter table iq_questions
  add column if not exists bucket text not null default 'medium',
  add column if not exists is_active boolean not null default true;
create index if not exists idx_iq_bucket on iq_questions(bucket);
create index if not exists idx_iq_active on iq_questions(is_active);
