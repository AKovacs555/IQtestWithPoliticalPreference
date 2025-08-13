import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';
import { waitForSession } from '../lib/waitForSession';

function getCodeFromUrl(): string | null {
  const u = new URL(window.location.href);
  const fromHash = u.hash.includes('?') ? new URLSearchParams(u.hash.split('?')[1]).get('code') : null;
  return fromHash ?? u.searchParams.get('code');
}

export default function AuthCallback() {
  const navigate = useNavigate();
  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        // 1) セッションが無ければ code 交換
        const first = await supabase.auth.getSession();
        if (!first.data.session) {
          const code = getCodeFromUrl();
          if (code) {
            const { error } = await supabase.auth.exchangeCodeForSession(code);
            if (error) {
              console.error('[auth] exchange error', error);
              if (alive) navigate('/', { replace: true });
              return;
            }
          }
        }
        // 2) ensure: app_users upsert（返りの is_admin を採用）
        let ensuredAdmin = false;
        try {
          const token = (await supabase.auth.getSession()).data.session?.access_token;
          if (token) {
            const resp = await fetch('/user/ensure', {
              method: 'POST',
              headers: { Authorization: `Bearer ${token}` },
              credentials: 'include',
            }).catch(() => undefined);
            try {
              const js = await resp?.json();
              ensuredAdmin = Boolean(js?.is_admin);
            } catch {}
          }
        } catch {}
        // 3) refresh してから、セッション確定を待つ（モバイルSaf対策）
        await supabase.auth.refreshSession().catch(() => {});
        const sess = await waitForSession(7000).catch((e) => {
          console.warn('[auth] waitForSession timeout', e);
          return null;
        });
        const isAdmin =
          ensuredAdmin ||
          Boolean(sess?.user?.app_metadata?.is_admin) ||
          Boolean((sess as any)?.user?.user_metadata?.is_admin) ||
          Boolean((sess as any)?.user?.is_admin);

        // 4) 遷移（管理者は /admin、それ以外は /）
        if (alive) {
          if (isAdmin) navigate('/admin', { replace: true });
          else navigate('/', { replace: true });
        }
      } catch (e) {
        console.error('[auth] callback fatal', e);
        if (alive) navigate('/', { replace: true });
      }
    })();

    return () => {
      alive = false;
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

