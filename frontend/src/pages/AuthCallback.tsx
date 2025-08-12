import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if ((event === 'INITIAL_SESSION' || event === 'SIGNED_IN') && session) {
        navigate('/', { replace: true });
      }
    });
    return () => {
      subscription.unsubscribe();
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

