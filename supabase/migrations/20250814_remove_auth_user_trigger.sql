-- Supabase Authユーザー作成時の不要なトリガーを削除し、エラーを防止するマイグレーション
begin;
  -- auth.usersに対する新規ユーザー挿入トリガーを削除
  drop trigger if exists handle_new_user on auth.users;
  drop trigger if exists create_user_profile on auth.users;
  -- 上記トリガーに関連する関数も削除（存在すれば）
  drop function if exists public.handle_new_user() cascade;
  drop function if exists public.create_user_profile() cascade;
commit;
