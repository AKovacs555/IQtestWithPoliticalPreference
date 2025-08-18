-- Rename custom users table to avoid conflict with Supabase auth.users
alter table public.users rename to app_users;

-- Update foreign key constraints to reference app_users
alter table public.survey_daily_progress
  drop constraint if exists survey_daily_progress_user_id_fkey,
  add constraint survey_daily_progress_user_id_fkey
    foreign key (user_id) references public.app_users(hashed_id) on delete cascade;


alter table public.referral_rewards
  drop constraint if exists referral_rewards_referrer_id_fkey,
  drop constraint if exists referral_rewards_referred_id_fkey,
  add constraint referral_rewards_referrer_id_fkey
    foreign key (referrer_id) references public.app_users(hashed_id) on delete cascade,
  add constraint referral_rewards_referred_id_fkey
    foreign key (referred_id) references public.app_users(hashed_id) on delete cascade;

alter table public.referrals
  drop constraint if exists referrals_invitee_user_fkey,
  add constraint referrals_invitee_user_fkey
    foreign key (invitee_user) references public.app_users(hashed_id) on delete cascade;

-- Ensure row level security remains enabled
alter table public.app_users enable row level security;
