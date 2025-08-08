import React from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import usePersistedLang from '../hooks/usePersistedLang';
import Navbar from './Navbar';
import Footer from './Footer';

export default function AppShell({ children }) {
  usePersistedLang();
  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <a href="#main" className="sr-only focus:not-sr-only">
        Skip to content
      </a>
      <Box component="header" sx={{ position: 'sticky', top: 0, zIndex: (theme) => theme.zIndex.appBar }}>
        <Navbar />
      </Box>
      <Container id="main" component="main" maxWidth="sm" sx={{ flexGrow: 1, py: 2 }}>
        {children}
      </Container>
      <Footer />
    </Box>
  );
}
