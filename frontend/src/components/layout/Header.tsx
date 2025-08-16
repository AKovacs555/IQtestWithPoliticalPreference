import React from 'react';
import { Box } from '@mui/material';

export default function Header() {
  return (
    <Box
      data-b-spec="header-no-tabs"
      className="sticky top-0 z-50 glass-surface"
      style={{ paddingTop: 4, paddingBottom: 4 }}
    />
  );
}
