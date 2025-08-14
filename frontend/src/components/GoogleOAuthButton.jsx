import React from 'react';
import Button from '@mui/material/Button';
import { signInWithGoogle } from '../lib/auth';

export default function GoogleOAuthButton({ fullWidth = true, size = 'medium', sx }) {
  const disabled = import.meta.env.VITE_DISABLE_GOOGLE === 'true';
  if (disabled) return null;

  const handleClick = () => {
    signInWithGoogle().catch(err => console.error(err));
  };

  return (
    <Button onClick={handleClick} variant="contained" fullWidth={fullWidth} size={size} sx={sx}>
      Continue with Google
    </Button>
  );
}
