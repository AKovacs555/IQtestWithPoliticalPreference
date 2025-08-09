import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';

export default function AuthCallback() {
  const navigate = useNavigate();
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
        navigate('/dashboard', { replace: true });
      } catch (e) {
        console.error('Auth callback failed', e);
        navigate('/?auth_error=1', { replace: true });
      }
    };
    doExchange();
  }, [navigate]);
  return null;
}
