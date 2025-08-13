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
    let cleanup: (() => void) | undefined;

    (async () => {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        const code = getCodeFromUrl();
        if (code) {
          const { error } = await supabase.auth.exchangeCodeForSession(code);
          if (error) console.error('exchange error', error);
        }
      }

      // app_users upsert（認可ヘッダ付き）
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

      // ここで onAuthStateChange を待つ（確実にセッションが載ってから遷移）
      const { data: sub } = supabase.auth.onAuthStateChange((_ev, sess) => {
        if (!mounted) return;
        if (sess) navigate('/', { replace: true });
      });
      cleanup = () => sub.subscription.unsubscribe();
      await supabase.auth.refreshSession(); // 念のため
      setTimeout(() => mounted && navigate('/', { replace: true }), 1200);
    })();

    return () => {
      mounted = false;
      cleanup?.();
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

