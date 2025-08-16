import React from 'react';
import { Box } from '@mui/material';
import { useLocation } from 'react-router-dom';
import Logo from '../Logo';

export default function Header() {
  const location = useLocation();
  const path = location.pathname;
  const isHomeOrLogin = path === '/' || path === '/login';

  return (
    <Box
      data-b-spec="header-no-tabs"
      className={`sticky top-0 z-50 glass-surface flex items-center ${isHomeOrLogin ? 'justify-center' : 'justify-between'} px-4 py-1`}
    >
      <Logo />
      {/* Other header elements can be added here */}
    </Box>
  );
}
