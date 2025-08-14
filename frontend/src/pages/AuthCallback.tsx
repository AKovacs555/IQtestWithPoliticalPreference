import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

function getCodeFromUrl(): string | null {
  const u = new URL(window.location.href);
  // HashRouterでも SearchRouter でも両対応
  const fromHash = u.hash.includes('?') ? new URLSearchParams(u.hash.split('?')[1]).get('code') : null;
  return fromHash ?? u.searchParams.get('code');
}

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    let mounted = true;
    (async () => {
      // 0) 既にセッションがあるなら即ホームへ
      const first = await supabase.auth.getSession();
      if (first.data.session) {
        if (mounted) navigate('/', { replace: true });
        return;
      }
      // 1) コードとコードベリファイアが揃っていれば交換
      const code = getCodeFromUrl();
      const verifierKey = `${supabase.auth.storageKey}-code-verifier`;
      const codeVerifier = window.localStorage.getItem(verifierKey);
      if (code && codeVerifier) {
        const { error } = await (supabase.auth as any).exchangeCodeForSession({
          authCode: code,
          codeVerifier,
        });
        if (error) console.error('[AuthCallback] exchangeCodeForSession error', error);
      } else {
        console.error('[AuthCallback] missing auth code or code verifier');
      }
      // 2) プロフィール upsert（非同期で fire-and-forget）
      const token = (await supabase.auth.getSession()).data.session?.access_token;
      if (token) {
        fetch('/user/ensure', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          credentials: 'include',
        }).catch(() => {});
      }
      // 3) 最終遷移
      if (mounted) navigate('/', { replace: true });
    })();
    return () => {
      mounted = false;
    };
  }, [navigate]);
  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

