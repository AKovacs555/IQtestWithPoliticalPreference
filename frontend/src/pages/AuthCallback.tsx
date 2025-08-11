import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      const { error } = await supabase.auth.exchangeCodeForSession(
        window.location.href,
      );
      if (error) console.error(error);
      navigate('/', { replace: true });
    })();
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}
