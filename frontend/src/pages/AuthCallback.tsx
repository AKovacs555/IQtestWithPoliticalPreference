import { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import { useNavigate } from 'react-router-dom';

function extractAuthCodeFromUrl(): string | null {
  const url = new URL(window.location.href);
  // HashRouter case: "#/auth/callback?code=..."
  const hash = url.hash; // e.g. "#/auth/callback?code=123&state=..."
  const hashQs = hash.includes('?') ? hash.split('?')[1] : '';
  const fromHash = new URLSearchParams(hashQs).get('code');
  // BrowserRouter case: "/auth/callback?code=..."
  const fromSearch = url.searchParams.get('code');
  return fromHash || fromSearch;
}

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        // 1) If detectSessionInUrl ran, this already exchanged and stored a session.
        const { data } = await supabase.auth.getSession();

        // 2) Fallback: no session yet -> do manual exchange from URL
        if (!data.session) {
          const code = extractAuthCodeFromUrl();
          if (code) {
            const { error } = await supabase.auth.exchangeCodeForSession(code);
            if (error) throw error;
          }
        }
      } catch (e) {
        console.error('Auth callback error:', e);
      } finally {
        if (mounted) navigate('/', { replace: true });
      }
    })();

    return () => {
      mounted = false;
    };
  }, [navigate]);

  return <div style={{ padding: 24 }}>Signing you in…</div>;
}

