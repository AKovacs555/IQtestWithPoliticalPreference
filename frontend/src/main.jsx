import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, HashRouter } from 'react-router-dom';
// Build trigger comment

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then((rs) => rs.forEach((r) => r.unregister()));
  if (window.caches?.keys) {
    caches.keys().then((keys) => keys.forEach((k) => caches.delete(k)));
  }
}

// Bust runtime cache once per deploy
// ※ OAuth コールバック中（URL に code/access_token/error を含む）は絶対にリロード・書き換えしない
try {
  const hasOAuthParams = /[?#].*(code=|access_token=|error=)/.test(window.location.href);
  const v = import.meta.env?.VITE_COMMIT_SHA || '';
  const prev = localStorage.getItem('app_version') || '';
  if (!hasOAuthParams && v && prev !== v) {
    localStorage.setItem('app_version', v);
    // ここでは現在の URL をそのまま再読み込み（ハッシュ含む）
    window.location.replace(window.location.href);
  }
} catch {}

// --- 重要: React 起動前にコールバックURLを正規化（HashRouter でも確実に /auth/callback をマウントさせる）
(function normalizeOAuthCallbackUrl() {
  const u = new URL(window.location.href);
  const hasCode = u.searchParams.has('code') || u.hash.includes('code=');
  const isOnCallback = /^#\/auth\/callback/.test(u.hash);
  // 例: "/?code=...#/auth/callback" → "/#/auth/callback?code=..."
  if (import.meta.env.PROD && hasCode && !isOnCallback) {
    const query = u.search || '';
    window.location.replace(`/#/auth/callback${query}`);
  }
})();

const Router = import.meta.env.PROD ? HashRouter : BrowserRouter;

// In production we use HashRouter; if someone lands on a path like /auth/callback
// without a hash, redirect to the hash equivalent so routes resolve correctly.
if (import.meta.env.PROD && !location.hash && location.pathname !== '/') {
  location.replace(`/#${location.pathname}${location.search}${location.hash}`);
}
import App from './pages/App';
import { SessionProvider, useSession } from './hooks/useSession';
import './i18n';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import '@fontsource-variable/inter';
import './styles.css';
import './styles/global.css';
import { getTheme, ColorModeContext } from './theme';

function Root() {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const [mode, setMode] = React.useState(
    () => localStorage.getItem('theme') || (prefersDark ? 'dark' : 'light'),
  );
  const { loading } = useSession();

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode);
    localStorage.setItem('theme', mode);
  }, [mode]);

  return (
    <ColorModeContext.Provider value={{ mode, setMode }}>
      <ThemeProvider theme={getTheme(mode)}>
        <CssBaseline />
        {!loading ? <App /> : <div style={{ padding: 24 }}>Loading…</div>}
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

createRoot(document.getElementById('root')).render(
  <Router>
    <SessionProvider>
      <Root />
    </SessionProvider>
  </Router>,
);
