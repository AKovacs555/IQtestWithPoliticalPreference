import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, HashRouter } from 'react-router-dom';
// Build trigger comment

const Router = import.meta.env.PROD ? HashRouter : BrowserRouter;
import App from './pages/App';
import { SessionProvider } from './hooks/useSession';
import './i18n';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import '@fontsource-variable/inter';
import './styles.css';
import './styles/global.css';
import { theme } from './theme';

createRoot(document.getElementById('root')).render(
  <Router>
    <SessionProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </SessionProvider>
  </Router>
);
