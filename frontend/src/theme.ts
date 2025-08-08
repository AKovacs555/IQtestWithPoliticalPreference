import { createTheme } from '@mui/material/styles';
import React from 'react';

export const ColorModeContext = React.createContext<{ mode: 'light' | 'dark'; setMode: (mode: 'light' | 'dark') => void }>({
  mode: 'light',
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  setMode: () => {},
});

export const getTheme = (mode: 'light' | 'dark') =>
  createTheme({
    palette: {
      mode,
      ...(mode === 'dark'
        ? {
            background: { default: '#0b1220', paper: '#0f172a' },
            text: { primary: '#e5e7eb', secondary: '#cbd5e1' },
            primary: { main: '#60a5fa' },
            secondary: { main: '#f59e0b' },
          }
        : {
            background: { default: '#ffffff', paper: '#ffffff' },
            text: { primary: '#111827', secondary: '#374151' },
            primary: { main: '#2563eb' },
            secondary: { main: '#f59e0b' },
          }),
    },
    typography: {
      fontFamily:
        '"Inter", system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial',
      fontSize: 16,
      body1: { lineHeight: 1.55 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    shape: { borderRadius: 12 },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          ':root': { '--tap-min': '48px' },
          'button, a, [role="button"]': { minHeight: 'var(--tap-min)' },
          '@media (prefers-reduced-motion: reduce)': {
            '*': { animation: 'none !important', transition: 'none !important' },
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          colorDefault: {
            backgroundColor:
              mode === 'dark'
                ? 'rgba(15,23,42,0.85)'
                : 'rgba(255,255,255,0.85)',
            backdropFilter: 'blur(8px)',
          },
        },
      },
    },
  });
