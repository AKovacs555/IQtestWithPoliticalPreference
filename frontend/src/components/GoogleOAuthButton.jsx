import React from 'react';
import { supabase } from '../lib/supabaseClient';

export default function GoogleOAuthButton() {
  const handleGoogle = async () => {
    await supabase.auth.signInWithOAuth({ provider: 'google' });
  };

  return (
    <button
      type="button"
      onClick={handleGoogle}
      className="w-full py-2 mt-4 text-white bg-red-600 rounded hover:bg-red-700"
    >
      Sign in with Google
    </button>
  );
}
