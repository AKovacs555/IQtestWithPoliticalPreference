import React, { useRef } from 'react';
import Button from '@mui/material/Button';
import HCaptcha from '@hcaptcha/react-hcaptcha';
import { signInWithGoogle } from '../lib/auth';

export default function GoogleOAuthButton({ fullWidth = true, size = 'medium', sx }) {
  const disabled = import.meta.env.VITE_DISABLE_GOOGLE === 'true';
  const siteKey = import.meta.env.VITE_HCAPTCHA_SITEKEY;
  const captchaRef = useRef(null);
  if (disabled) return null;

  const handleVerify = (token) => {
    signInWithGoogle(token).catch(err => console.error(err));
  };

  const handleClick = () => {
    if (siteKey && captchaRef.current) {
      captchaRef.current.execute();
    } else {
      signInWithGoogle().catch(err => console.error(err));
    }
  };

  return (
    <>
      {siteKey && (
        <HCaptcha
          ref={captchaRef}
          sitekey={siteKey}
          size="invisible"
          onVerify={handleVerify}
        />
      )}
      <Button onClick={handleClick} variant="contained" fullWidth={fullWidth} size={size} sx={sx}>
        Continue with Google
      </Button>
    </>
  );
}
