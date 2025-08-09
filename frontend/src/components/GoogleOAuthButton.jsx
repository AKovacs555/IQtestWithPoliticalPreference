import React from 'react';
import { supabase } from '../lib/supabaseClient';

export default function GoogleOAuthButton() {
  async function signInWithGoogle() {
    const redirectTo = window.location.origin + '/#/auth/callback';
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
