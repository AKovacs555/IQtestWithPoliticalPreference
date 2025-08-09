import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';

export default function AuthCallback() {
  const nav = useNavigate();
  useEffect(() => {
    (async () => {
      // Exchange code for session and clean the URL
      await supabase.auth.exchangeCodeForSession(window.location.href);
      nav('/dashboard', { replace: true });
    })();
  }, []);
  return null;
}
