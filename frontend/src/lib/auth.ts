import { supabase } from './supabaseClient';
const redirectTo = `${window.location.origin}/auth/callback`;

export async function signInWithGoogle() {
  try {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo,
        // refresh token を得るために offline + consent を付与
        queryParams: { access_type: 'offline', prompt: 'consent' },
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

export async function signOut() {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}
