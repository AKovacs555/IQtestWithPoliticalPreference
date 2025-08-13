import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

function getCodeFromUrl(): string | null {
  const u = new URL(window.location.href);
  // HashRouter 末尾クエリにも対応（#/auth/callback?code=...）
  const fromHash = u.hash.includes('?') ? new URLSearchParams(u.hash.split('?')[1]).get('code') : null;
  return fromHash ?? u.searchParams.get('code');
}

function stripOAuthParams() {
  // code/state/error を URL から取り除く
  const u = new URL(window.location.href);
  ['code', 'state', 'error'].forEach((k) => u.searchParams.delete(k));
  try {
    window.history.replaceState({}, '', u.toString());
  } catch {
    // ignore
  }
}

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    let alive = true;
    const goHomeHard = () => {
      if (!alive) return;
      // HashRouterでトップページへリダイレクト
      window.location.replace(`${window.location.origin}/#/`);
    };

    (async () => {
      try {
        // 1) 初期セッション確認 → なければ code 交換
        const first = await supabase.auth.getSession();
        if (!first.data.session) {
          const code = getCodeFromUrl();
          if (code) {
            const { error } = await supabase.auth.exchangeCodeForSession(code);
            if (error) {
              console.error('[auth] exchange error', error);
              stripOAuthParams();
              goHomeHard();
              return;
            }
          }
        }
        // 2) app_users upsert（失敗しても遷移はブロックしない）
        try {
          const token = (await supabase.auth.getSession()).data.session?.access_token;
          if (token) {
            await fetch('/user/ensure', {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
              credentials: 'include',
            });
          }
        } catch {}
        // 3) セッション取得できたら管理者か判定し、適切な画面へリダイレクト
        const { data: sessionData } = await supabase.auth.getSession();
        const session = sessionData.session;
        stripOAuthParams();
        if (session?.user) {
          const user = session.user;
          const isAdmin =
            user.is_admin === true ||
            user.user_metadata?.is_admin === true ||
            user.app_metadata?.is_admin === true;
          const destHash = isAdmin ? '/#/admin' : '/#/';
          window.location.replace(`${window.location.origin}${destHash}`);
        } else {
          // セッションが無い場合はホームへ
          goHomeHard();
        }
      } catch (e) {
        console.error('[auth] callback fatal', e);
        goHomeHard();
      }
    })();

    return () => {
      alive = false;
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

