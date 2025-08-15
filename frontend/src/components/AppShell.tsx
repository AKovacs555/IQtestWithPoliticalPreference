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
      data-b-spec="appshell-v1"
      sx={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}
      className="font-sans text-[var(--text)] bg-transparent"
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
