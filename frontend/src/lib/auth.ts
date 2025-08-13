import { supabase } from './supabaseClient';

// Google 側の Redirect URI はフラグメント(#)不可。非ハッシュの /auth/callback を使う
const redirectTo = `${window.location.origin}/auth/callback`;

export async function signInWithGoogle(captchaToken?: string) {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo,
      queryParams: { prompt: 'select_account' }, // 必要に応じて access_type=offline も追加可
      ...(captchaToken ? { captchaToken } : {}),
    },
  });
  if (error) throw error;
}

export async function signUpWithEmail(email: string, password: string) {
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: redirectTo }
  });
  if (error) throw error;
}

export async function signInWithEmail(email: string, password: string) {
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
}

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}
