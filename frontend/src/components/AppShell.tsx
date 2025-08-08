import React, { PropsWithChildren } from 'react';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import usePersistedLang from '../hooks/usePersistedLang';
import Navbar from './Navbar';
import Footer from './Footer';

export default function AppShell({ children }: PropsWithChildren) {
  usePersistedLang();
  return (
    <Box sx={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
      <Box component="header" className="border-b border-gray-200" sx={{ py: 1.5, px: { xs: 1, md: 2 }, position: 'sticky', top: 0, zIndex: (theme) => theme.zIndex.appBar }}>
        <Navbar />
      </Box>
      <Container component="main" maxWidth="lg" sx={{ flex: 1, px: { xs: 1.5, md: 2 }, py: { xs: 2, md: 3 } }}>
        {children}
      </Container>
      <Footer />
      <Box component="footer" sx={{ display: { xs: 'block', md: 'none' }, height: 'env(safe-area-inset-bottom)' }} />
    </Box>
  );
}
