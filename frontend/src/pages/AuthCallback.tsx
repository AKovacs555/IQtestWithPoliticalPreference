import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

function getCodeFromUrl(): string | null {
  const u = new URL(window.location.href);
  // BrowserRouter基本：search優先、念のためhash内も最後に見る
  return (
    u.searchParams.get('code') ||
    (u.hash.includes('?') ? new URLSearchParams(u.hash.split('?')[1]).get('code') : null)
  );
}

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    let mounted = true;
    (async () => {
      // 0) 既存セッションの有無に関わらず /user/ensure を実行する
      const first = await supabase.auth.getSession();
      if (!first.data.session) {
        // コードとコードベリファイアが揃っていれば交換
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
      }

      // 1) ユーザープロフィールDB upsertを待つ
      try {
        const token = (await supabase.auth.getSession()).data.session?.access_token;
        if (token) {
          const resp = await fetch('/user/ensure', {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
            credentials: 'include',
          });
          if (!resp.ok) {
            const msg = await resp.text();
            console.error('[AuthCallback] /user/ensure failed', msg);
            alert('Failed to ensure user profile');
          }
        }
      } catch (e) {
        console.warn('[AuthCallback] /user/ensure error', e);
        alert('Failed to ensure user profile');
      }

      // 2) JWT を更新して app_metadata.is_admin を確実に反映
      try {
        await supabase.auth.refreshSession();
      } catch (e) {
        console.warn('[AuthCallback] refreshSession error', e);
      }

      if (mounted) navigate('/', { replace: true });
    })();
    return () => {
      mounted = false;
    };
  }, [navigate]);
  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

