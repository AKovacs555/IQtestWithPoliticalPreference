import { useState, useEffect } from 'react';

export default function useAuth() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      // TODO: optionally decode and validate the token, fetch user info if needed
      setUser({ token });
    }
  }, []);

  return { user };
}
