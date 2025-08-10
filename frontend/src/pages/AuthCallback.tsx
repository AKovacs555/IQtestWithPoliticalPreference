import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabaseClient';

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    const sp = new URLSearchParams(window.location.search);
    const code = sp.get('code');
    const error = sp.get('error') || sp.get('error_description');

    async function run() {
      try {
        if (code) {
          const { error: exErr } = await supabase.auth.exchangeCodeForSession(code);
          if (exErr) {
            // eslint-disable-next-line no-console
            console.error('exchangeCodeForSession error', exErr);
          }
          const { data } = await supabase.auth.getSession();
          if (data?.session) {
            localStorage.setItem('authToken', data.session.access_token);
            localStorage.setItem('user_id', data.session.user?.id || '');
          }
        } else if (error) {
          // eslint-disable-next-line no-console
          console.error('OAuth callback error:', error);
        }
      } finally {
        navigate('/', { replace: true });
      }
    }

    run();
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}
