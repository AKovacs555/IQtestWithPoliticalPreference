-- Add missing email column and create profile trigger for new auth users
alter table public.app_users
  add column if not exists email text;

create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.app_users (id, hashed_id, email)
  values (new.id, new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

drop policy if exists "Allow self access to app_users" on public.app_users;
create policy "Allow self access to app_users"
  on public.app_users for select, update
  using (id = auth.uid())
  with check (id = auth.uid());
