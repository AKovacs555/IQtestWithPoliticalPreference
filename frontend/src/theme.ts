import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#2563EB' }, // blue-600
    secondary: { main: '#F59E0B' }, // amber-500
    background: { default: '#FFFFFF', paper: '#FFFFFF' },
    text: { primary: '#111827', secondary: '#374151' }, // high contrast
  },
  typography: {
    fontFamily: '"Inter Variable", system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial',
    fontSize: 16,            // base 16px for readability on mobile
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    body1: { lineHeight: 1.55 },  // 1.4–1.6 for comfortable reading
    button: { textTransform: 'none', fontWeight: 600 }
  },
  shape: { borderRadius: 12 }
});
