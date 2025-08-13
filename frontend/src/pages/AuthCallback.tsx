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

    // 先に購読を確立（効果のクリーンアップで確実に解除）
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_ev, sess) => {
      if (!mounted) return;
      if (sess) {
        if (import.meta.env.DEV) console.log('[auth] signed in', sess.user?.id);
        navigate('/', { replace: true });
      }
    });

    (async () => {
      // まだセッションが無ければ code を交換
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
        if (token) {
          await fetch('/user/ensure', {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            credentials: 'include',
          });
        }
      } catch (e) {
        console.warn('/user/ensure failed', e);
      }
      // 念のためリフレッシュ（onAuthStateChange が拾います）
      await supabase.auth.refreshSession();
    })();

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

