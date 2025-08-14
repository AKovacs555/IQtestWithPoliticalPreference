import React from 'react';
import Box from '@mui/material/Box';
import Navbar from '../Navbar';

export default function Header() {
  return (
    <Box
      component="header"
      className="sticky top-0 z-50 backdrop-blur-md bg-[var(--glass)] border-b border-[var(--border)]"
      sx={{ px: { xs: 1, md: 2 }, py: 1.5 }}
    >
      <Navbar />
    </Box>
  );
}
