import { createTheme } from '@mui/material/styles';
import React from 'react';

declare module '@mui/material/styles' {
  interface Palette {
    custom: {
      surface: string;
      muted: string;
      border: string;
    };
  }
  interface PaletteOptions {
    custom?: {
      surface?: string;
      muted?: string;
      border?: string;
    };
  }
}

export const ColorModeContext = React.createContext<{ mode: 'light' | 'dark'; setMode: (mode: 'light' | 'dark') => void }>({
  mode: 'light',
  // eslint-disable-next-line @typescript-eslint/no-empty-function
  setMode: () => {},
});

export const getTheme = (mode: 'light' | 'dark') => {
  const isDark = mode === 'dark';
  const base = createTheme();
  return createTheme({
    palette: {
      mode,
      primary: { main: isDark ? '#60a5fa' : '#2563eb', contrastText: '#fff' },
      secondary: { main: '#f59e0b', contrastText: '#111827' },
      success: { main: '#16a34a', contrastText: '#fff' },
      warning: { main: '#eab308', contrastText: '#111827' },
      info: { main: '#0ea5e9', contrastText: '#fff' },
      background: {
        default: isDark ? '#0b1220' : '#ffffff',
        paper: isDark ? '#0f172a' : '#ffffff',
      },
      text: {
        primary: isDark ? '#e5e7eb' : '#111827',
        secondary: isDark ? '#cbd5e1' : '#374151',
      },
      custom: {
        surface: isDark ? '#1e293b' : '#f9fafb',
        muted: isDark ? '#475569' : '#6b7280',
        border: isDark ? '#334155' : '#e5e7eb',
      },
    },
    spacing: 8,
    typography: {
      fontFamily:
        '"Inter", system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial',
      fontSize: 16,
      h1: { fontSize: '2rem', fontWeight: 700, lineHeight: 1.3 },
      h2: { fontSize: '1.5rem', fontWeight: 700, lineHeight: 1.35 },
      h3: { fontSize: '1.25rem', fontWeight: 600, lineHeight: 1.4 },
      h4: { fontSize: '1.125rem', fontWeight: 600, lineHeight: 1.45 },
      h5: { fontSize: '1rem', fontWeight: 600, lineHeight: 1.5 },
      h6: { fontSize: '0.875rem', fontWeight: 600, lineHeight: 1.5 },
      body1: { lineHeight: 1.55 },
      body2: { lineHeight: 1.55 },
      caption: { lineHeight: 1.4 },
      button: { textTransform: 'none', fontWeight: 600 },
    },
    shape: { borderRadius: 12 },
    shadows: base.shadows,
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          ':root': { '--tap-min': '48px' },
          html: { fontSize: '100%' },
          'button, a, [role="button"]': { minHeight: 'var(--tap-min)' },
          '@media (prefers-reduced-motion: reduce)': {
            '*': { animation: 'none !important', transition: 'none !important' },
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          colorDefault: {
            backgroundColor: isDark
              ? 'rgba(15,23,42,0.85)'
              : 'rgba(255,255,255,0.85)',
            backdropFilter: 'blur(8px)',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            ':focus-visible': {
              outline: '2px solid currentColor',
              outlineOffset: 2,
            },
          },
        },
      },
    },
  });
};
