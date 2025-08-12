import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';

export default function AuthCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const url = new URL(window.location.href);
      let code = url.searchParams.get('code');
      if (!code && url.hash.includes('?')) {
        const hashParams = new URLSearchParams(url.hash.split('?')[1]);
        code = hashParams.get('code');
      }
      if (!code) {
        navigate('/', { replace: true });
        return;
      }
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        try {
          const { error } = await supabase.auth.exchangeCodeForSession(window.location.href);
          if (error) throw error;
          try {
            await fetch(`${import.meta.env.VITE_API_BASE!}/user/ensure`, { method: 'POST' });
          } catch {}
        } catch (e) {
          console.error('Auth callback failed', e);
          setError('Sign-in failed.');
          return;
        }
      }
      navigate('/', { replace: true });
    })();
  }, [navigate]);

  if (error) {
    return (
      <div>
        <p>{error}</p>
        <button onClick={() => navigate('/')}>Go home</button>
      </div>
    );
  }
  return <div>Signing you in…</div>;
}
