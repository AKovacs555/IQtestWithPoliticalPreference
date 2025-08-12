import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    let mounted = true;
    (async () => {
      // detectSessionInUrl already exchanged the code.
      await supabase.auth.getSession();
      if (mounted) navigate('/', { replace: true });
    })();
    return () => {
      mounted = false;
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

