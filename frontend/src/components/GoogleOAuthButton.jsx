import React from 'react';
import { signInWithGoogle } from '../lib/auth';

export default function GoogleOAuthButton() {
  const disabled = import.meta.env.VITE_DISABLE_GOOGLE === 'true';
  if (disabled) return null;

  function handleClick() {
    signInWithGoogle().catch(err => console.error(err));
  }

  return (
    <button onClick={handleClick} className="btn btn-primary w-full mt-4">
      Continue with Google
    </button>
  );
}
