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
          // PKCEコードをセッションに交換
          const { error: exErr } = await supabase.auth.exchangeCodeForSession(code);
          if (exErr) {
            // eslint-disable-next-line no-console
            console.error('exchangeCodeForSession error', exErr);
          }
          // 交換後にセッションを取得してローカルストレージに保存
          const { data: sessionData } = await supabase.auth.getSession();
          if (sessionData?.session) {
            localStorage.setItem('authToken', sessionData.session.access_token);
            localStorage.setItem('user_id', sessionData.session.user?.id || '');
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
