import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

function getCodeFromUrl(): string | null {
  const u = new URL(window.location.href);
  // HashRouter の場合でも google は # を返さないため、基本は search で拾える。
  const fromHash = u.hash.includes('?')
    ? new URLSearchParams(u.hash.split('?')[1]).get('code')
    : null;
  return fromHash ?? u.searchParams.get('code');
}

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    let alive = true;
    const goHome = () => {
      if (!alive) return;
      // React Router が何らかの理由で遷移を握り潰すケースに備えて二段構え
      navigate('/', { replace: true });
      // HashRouter では location.replace で確実に脱出できる
      setTimeout(() => alive && window.location.replace('/#/'), 200);
    };

    (async () => {
      const current = (await supabase.auth.getSession()).data.session;
      if (!current) {
        const code = getCodeFromUrl();
        if (code) {
          // PKCE コード → セッションへ交換（localStorage に保存され、SIGNED_IN が発火）
          const { error } = await supabase.auth.exchangeCodeForSession(code);
          if (error) console.error('[auth] exchange error:', error);
        }
      }

      // app_users upsert（失敗は無視）
      try {
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        if (token) {
          await fetch('/user/ensure', {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
              'Cache-Control': 'no-store',
            },
            credentials: 'include',
          });
        }
      } catch (e) {
        console.warn('[auth] /user/ensure failed', e);
      }

      // 念のためセッションをリフレッシュ（onAuth で拾えない環境の保険）
      await supabase.auth.refreshSession().catch(() => {});
      goHome();
    })();

    return () => {
      alive = false;
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

