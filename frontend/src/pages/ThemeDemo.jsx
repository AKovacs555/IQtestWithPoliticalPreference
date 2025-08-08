import React from 'react';
import { Stack, Typography, Button, Paper } from '@mui/material';
import AppShell from '../components/AppShell';

export default function ThemeDemo() {
  return (
    <AppShell>
      <Typography variant="h4" gutterBottom>
        Theme Tokens
      </Typography>
      <Stack spacing={2} direction="row" flexWrap="wrap">
        <Button variant="contained" color="primary">Primary</Button>
        <Button variant="contained" color="secondary">Secondary</Button>
        <Paper sx={{ p: 2 }}>Card Radius Demo</Paper>
      </Stack>
    </AppShell>
  );
}
