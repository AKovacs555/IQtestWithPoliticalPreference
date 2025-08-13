import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

function getCodeFromUrl(): string | null {
  const url = new URL(window.location.href);
  const hashQs = url.hash.includes('?') ? url.hash.split('?')[1] : '';
  return new URLSearchParams(hashQs).get('code') || url.searchParams.get('code');
}

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    (async () => {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        const code = getCodeFromUrl();
        if (code) {
          const { error } = await supabase.auth.exchangeCodeForSession(code);
          if (error) console.error('exchange error', error);
        }
      }

      // ensure app_users row exists
      try {
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        await fetch('/user/ensure', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token ?? ''}` },
          credentials: 'include',
        });
      } catch (e) {
        console.warn('/user/ensure failed', e);
      }

      // onAuthStateChange でセッション確定を待つ
      const { data: sub } = supabase.auth.onAuthStateChange((_ev, sess) => {
        if (!mounted) return;
        if (sess) {
          if (import.meta.env.DEV) console.log('[auth] signed in', sess.user?.id);
          navigate('/', { replace: true });
        }
      });
      // 念のため即時リフレッシュ
      await supabase.auth.refreshSession();
      setTimeout(() => {
        if (mounted) navigate('/', { replace: true });
      }, 1200);
      return () => sub.subscription.unsubscribe();
    })();

    return () => {
      mounted = false;
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

