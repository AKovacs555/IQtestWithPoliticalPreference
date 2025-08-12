import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';
import { fetchWithAuth } from '../lib/api';

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if ((event === 'INITIAL_SESSION' || event === 'SIGNED_IN') && session) {
        try {
          await fetchWithAuth('/user/ensure', {
            method: 'POST',
            body: JSON.stringify({}),
          });
        } catch {
          /* ignore */
        }
        const { data } = await supabase.auth.getSession();
        const isAdmin = Boolean(data.session?.user?.app_metadata?.is_admin);
        navigate(isAdmin ? '/admin' : '/', { replace: true });
      }
    });
    return () => {
      subscription.unsubscribe();
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

