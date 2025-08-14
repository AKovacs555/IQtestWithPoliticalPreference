import React from 'react';
import GoogleOAuthButton from '../components/GoogleOAuthButton.jsx';

export default function LoginPage() {
  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <GoogleOAuthButton />
    </div>
  );
}
