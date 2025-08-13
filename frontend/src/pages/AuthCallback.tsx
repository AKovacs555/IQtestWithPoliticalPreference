import { useEffect, useState } from 'react';
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
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    const goHomeSoft = () => {
      if (!alive) return;
      sessionStorage.setItem('skip_version_reload', '1');
      navigate('/', { replace: true });
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
              window.alert('Login failed: ' + error.message);
              stripOAuthParams();
              setErrorMsg('Login failed: ' + error.message);
              return;
            }
            const { data: sessionData, error: sessErr } =
              await supabase.auth.getSession();
            console.log(
              '[AuthCallback] Post-exchange session =',
              sessionData.session,
              sessErr,
            );
            if (!sessionData.session) {
              stripOAuthParams();
              setErrorMsg('Login failed: no session');
              return;
            }
          } else {
            setErrorMsg('Login failed: no code');
            stripOAuthParams();
            return;
          }
        }
        // 2) app_users upsert and get admin flag
        let isAdmin = false;
        try {
          const token = (await supabase.auth.getSession()).data.session?.access_token;
          if (token) {
            const res = await fetch('/user/ensure', {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
              credentials: 'include',
            });
            const json = await res.json().catch(() => ({}));
            isAdmin = json.is_admin === true;
            await supabase.auth.refreshSession();
          }
        } catch (e) {
          console.error('[auth] ensure failed', e);
        }
        // 3) セッション取得できたら管理者か判定し、適切な画面へリダイレクト
        const { data: sessionData } = await supabase.auth.getSession();
        const session = sessionData.session;
        stripOAuthParams();
        if (session?.user) {
          sessionStorage.setItem('skip_version_reload', '1');
          navigate(isAdmin ? '/admin' : '/', { replace: true });
        } else {
          setErrorMsg('Login failed: session missing');
        }
      } catch (e) {
        console.error('[auth] callback fatal', e);
        stripOAuthParams();
        setErrorMsg('Login failed');
      }
    })();

    return () => {
      alive = false;
    };
  }, [navigate]);

  return (
    <div style={{ padding: 24 }}>
      {errorMsg ? (
        <>
          <p>{errorMsg}</p>
          <button onClick={goHomeSoft}>Home</button>
        </>
      ) : (
        'Signing you in…'
      )}
    </div>
  );
}

