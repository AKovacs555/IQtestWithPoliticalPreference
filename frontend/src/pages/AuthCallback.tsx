import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        // Support both /auth/callback?code=... and /#/auth/callback?code=...
        const search = new URLSearchParams(window.location.search);
        let code = search.get('code');

        if (!code && window.location.hash) {
          const hashQuery = window.location.hash.split('?')[1] ?? '';
          if (hashQuery) {
            const hashParams = new URLSearchParams(hashQuery);
            code = hashParams.get('code') ?? undefined;
          }
        }

        if (!code) {
          console.error('Auth callback: missing OAuth code');
          navigate('/', { replace: true });
          return;
        }

        const { data, error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) throw error;

        const at = data.session?.access_token;
        const uid = data.session?.user?.id;
        if (at) localStorage.setItem('authToken', at);
        if (uid) localStorage.setItem('user_id', uid);

      } catch (e) {
        console.error('Auth callback failed', e);
      } finally {
        navigate('/', { replace: true });
      }
    })();
  }, [navigate]);

  return <div>Signing you in…</div>;
}
