import React from 'react';
import { supabase } from '../lib/supabase';

export default function GoogleOAuthButton() {
  const disabled = import.meta.env.VITE_DISABLE_GOOGLE === 'true';
  if (disabled) return null;

  async function signInWithGoogle() {
    const redirectTo = window.location.origin + '/auth/callback';
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo },
    });
  }

  return (
    <button onClick={signInWithGoogle} className="btn btn-primary w-full mt-4">
      Continue with Google
    </button>
  );
}
