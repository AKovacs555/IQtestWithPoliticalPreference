import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './pages/App';
import { SessionProvider } from './hooks/useSession';
import './i18n';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import './styles.css';

const theme = createTheme({
  typography: {
    fontFamily: 'Helvetica Neue, Roboto, sans-serif',
  },
  palette: {
    mode: 'light',
    primary: { main: '#1db954' },
    secondary: { main: '#0a84ff' },
    background: { default: '#f5f5f7' },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: { minWidth: 44, minHeight: 44 },
      },
    },
  },
});

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <SessionProvider>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </SessionProvider>
  </BrowserRouter>
);
