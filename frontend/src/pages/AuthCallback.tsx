import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

function getCodeFromUrl(): string | null {
  const u = new URL(window.location.href);
  const fromHash = u.hash.includes('?') ? new URLSearchParams(u.hash.split('?')[1]).get('code') : null;
  return fromHash ?? u.searchParams.get('code');
}

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    let alive = true;
    const goHome = () => alive && navigate('/', { replace: true });

    (async () => {
      try {
        // 1) まだセッションが無ければ code を交換
        const { data } = await supabase.auth.getSession();
        if (!data.session) {
          const code = getCodeFromUrl();
          if (code) {
            const { error } = await supabase.auth.exchangeCodeForSession(code);
            if (error) console.error('exchange error', error); // セッションはここで保存される
          }
        }
        // 2) プロフィール upsert（失敗しても遷移はブロックしない）
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        if (token) {
          fetch('/user/ensure', {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            credentials: 'include',
          }).catch(() => {});
        }
      } finally {
        goHome(); // イベント待ちは不要。直ちにホームへ
      }
    })();

    return () => {
      alive = false;
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

