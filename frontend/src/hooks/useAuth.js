import { useState, useEffect } from 'react';

function decode(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch {
    return {};
  }
}

export default function useAuth() {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('authToken');
    if (!token) return null;
    const payload = decode(token);
    return { token, ...payload };
  });

  useEffect(() => {
    const handleStorage = () => {
      const token = localStorage.getItem('authToken');
      if (!token) {
        setUser(null);
        return;
      }
      const payload = decode(token);
      setUser({ token, ...payload });
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  return { user };
}
