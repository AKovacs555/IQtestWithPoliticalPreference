import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, HashRouter } from 'react-router-dom';
// Build trigger comment

const Router = import.meta.env.PROD ? HashRouter : BrowserRouter;

// In production we use HashRouter; if someone lands on /admin/xyz without a hash,
// redirect to the hash equivalent so routes resolve correctly.
if (import.meta.env.PROD && !location.hash && location.pathname !== '/') {
  const path = location.pathname + location.search;
  location.replace('/#' + (path.startsWith('/') ? path : '/' + path));
}
import App from './pages/App';
import { SessionProvider } from './hooks/useSession';
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

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', mode);
    localStorage.setItem('theme', mode);
  }, [mode]);

  return (
    <ColorModeContext.Provider value={{ mode, setMode }}>
      <ThemeProvider theme={getTheme(mode)}>
        <CssBaseline />
        <App />
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
