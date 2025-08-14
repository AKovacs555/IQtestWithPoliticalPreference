import React, { PropsWithChildren } from 'react';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import usePersistedLang from '../hooks/usePersistedLang';
import Header from './layout/Header';
import Footer from './Footer';

export default function AppShell({ children }: PropsWithChildren) {
  usePersistedLang();
  return (
    <Box
      sx={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}
      className="bg-[linear-gradient(135deg,var(--bg-950),var(--bg-900),rgba(8,145,178,.20))] text-[var(--text)]"
    >
      <Header />
      <Container component="main" maxWidth="lg" sx={{ flex: 1, px: { xs: 1.5, md: 2 }, py: { xs: 2, md: 3 } }}>
        {children}
      </Container>
      <Footer />
      <Box component="footer" sx={{ display: { xs: 'block', md: 'none' }, height: 'env(safe-area-inset-bottom)' }} />
    </Box>
  );
}
