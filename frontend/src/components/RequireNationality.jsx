import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function RequireNationality({ children }) {
  const navigate = useNavigate();
  useEffect(() => {
    const nat = localStorage.getItem('nationality');
    if (!nat) {
      navigate('/select-nationality', { replace: true });
    }
  }, [navigate]);
  return children;
}
