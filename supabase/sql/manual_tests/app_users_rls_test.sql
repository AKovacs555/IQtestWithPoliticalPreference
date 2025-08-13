-- Test RLS on app_users by impersonating an authenticated user
begin;
  set local role authenticated;
  set local request.jwt.claims = '{"sub":"<auth.users.id>","role":"authenticated"}';
  select id, username, is_admin from public.app_users;
rollback;
