import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';

export default function AuthCallback() {
  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get('code');
    const doExchange = async () => {
      try {
        if (code) {
          await supabase.auth.exchangeCodeForSession(code);
        } else {
          // When detectSessionInUrl handled it already
          await supabase.auth.getSession();
        }
        window.location.replace('/');
      } catch (e) {
        console.error('Auth callback failed', e);
        window.location.replace('/?auth_error=1');
      }
    };
    doExchange();
  }, []);
  return null;
}
