import { supabase } from './supabaseClient';
const redirectTo = `${window.location.origin}/auth/callback`;

export async function signInWithGoogle() {
  try {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo,
        // UX重視：アカウント選択のみ促す（SupabaseのRTで永続化されるためoffline/consentは不要）
        queryParams: { prompt: 'select_account' },
      },
    });
    if (error) throw error;
  } catch (err: any) {
    console.error('Google sign-in failed', err);
    // eslint-disable-next-line no-alert
    alert(err.message || 'Google sign-in failed');
    throw err;
  }
}

export async function signUpWithEmail(email: string, password: string) {
  const { error } = await supabase.auth.signUp({
    email,
    password,
    // Email sign‑up does not require captcha tokens
    options: { emailRedirectTo: redirectTo },
  });
  if (error) throw error;
}

export async function signInWithEmail(email: string, password: string) {
  // Email sign‑in is performed without captcha verification
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) throw error;
}

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}
