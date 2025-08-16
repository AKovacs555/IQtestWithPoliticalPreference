import React from 'react';
import { Box } from '@mui/material';
import Logo from '../Logo';

export default function Header() {
  return (
    <Box
      component="header"
      className="sticky top-0 z-50 backdrop-blur-md bg-[var(--bg-glass)] border-b border-[var(--border-soft)]"
      sx={{ px: { xs: 8, md: 16 }, py: 2 }}
    >
      <div className="flex justify-center">
        <Logo />
      </div>
    </Box>
  );
}
