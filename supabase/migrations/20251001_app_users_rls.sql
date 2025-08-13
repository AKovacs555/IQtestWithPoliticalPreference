-- Enable row level security and add self-access policies for app_users
alter table public.app_users enable row level security;

drop policy if exists "Allow self access to app_users" on public.app_users;
drop policy if exists "select own profile" on public.app_users;
drop policy if exists "update own profile" on public.app_users;

create policy "select own profile"
  on public.app_users for select
  using (id = auth.uid());

create policy "update own profile"
  on public.app_users for update
  using (id = auth.uid())
  with check (id = auth.uid());
