import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';
import { fetchWithAuth } from '../lib/api';

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        // 1) pick up code from either ?code=... or #/auth/callback?code=...
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

        // 2) exchange code -> session (PKCE)
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) throw error;

        // 3) ensure app_users row exists (server will upsert)
        try {
          await fetchWithAuth('/user/ensure', { method: 'POST', body: JSON.stringify({}) });
        } catch (e) {
          console.warn('ensure profile failed; will rely on DB trigger or next fetch', e);
        }
      } catch (e) {
        console.error('Auth callback failed', e);
      } finally {
        // clear code from URL and go home
        navigate('/', { replace: true });
      }
    })();
  }, [navigate]);

  return <div>Signing you in…</div>;
}
