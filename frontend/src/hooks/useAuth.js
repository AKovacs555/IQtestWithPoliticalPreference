import { useState, useEffect } from 'react';

export default function useAuth() {
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('authToken');
    return token ? { token } : null;
  });

  useEffect(() => {
    const handleStorage = () => {
      const token = localStorage.getItem('authToken');
      setUser(token ? { token } : null);
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  return { user };
}
