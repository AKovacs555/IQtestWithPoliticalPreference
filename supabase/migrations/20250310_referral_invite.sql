alter table users add column if not exists invite_code text unique;
alter table users add column if not exists referred_by text;
create table if not exists referrals (
  id uuid primary key default gen_random_uuid(),
  inviter_code text not null,
  invitee_user text not null unique references users(hashed_id) on delete cascade,
  credited boolean not null default false,
  credited_at timestamptz
);
