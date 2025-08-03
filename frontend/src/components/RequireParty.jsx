import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export default function RequireParty({ children }) {
  const navigate = useNavigate();
  useEffect(() => {
    const party = localStorage.getItem('party_selected');
    if (!party) {
      navigate('/select-party', { replace: true });
    }
  }, [navigate]);
  return children;
}
