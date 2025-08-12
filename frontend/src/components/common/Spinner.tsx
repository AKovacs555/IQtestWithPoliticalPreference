import { Box, CircularProgress } from '@mui/material';
import React from 'react';

export default function Spinner() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 2 }}>
      <CircularProgress size={24} />
    </Box>
  );
}
