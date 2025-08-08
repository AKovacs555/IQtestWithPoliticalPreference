import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  spacing: 8,
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: 'Helvetica Neue, Roboto, sans-serif',
    fontSize: 16,
    button: { textTransform: 'none' },
  },
  palette: {
    mode: 'light',
    primary: { main: '#1db954', contrastText: '#ffffff' },
    secondary: { main: '#0a84ff', contrastText: '#ffffff' },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: { minWidth: 44, minHeight: 44 },
      },
    },
    MuiListItem: {
      styleOverrides: {
        root: { minHeight: 44 },
      },
    },
    MuiAppBar: {
      defaultProps: {
        elevation: 0,
      },
    },
    MuiCard: {
      styleOverrides: {
        root: { borderRadius: 12 },
      },
    },
  },
});

export default theme;
