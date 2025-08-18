import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSession } from '../hooks/useSession';

export default function QuizStart() {
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const { session } = useSession();
  const [error, setError] = React.useState(null);
  const apiBase = import.meta.env.VITE_API_BASE || '';

  React.useEffect(() => {
    async function start() {
      try {
        const headers = session?.access_token
          ? { Authorization: `Bearer ${session.access_token}` }
          : {};
        const res = await fetch(
          `${apiBase}/quiz/start?lang=${i18n.language}`,
          { headers, credentials: 'include' }
        );
        if (res.ok) {
          const data = await res.json();
          navigate(`/quiz/play?attempt_id=${data.attempt_id}`);
          return;
        }
        let err = {};
        try { err = await res.json(); } catch {}
        const code = err?.error || err?.detail?.error || err?.detail?.code;
        if (code === 'nationality_required') {
          navigate('/country');
          return;
        }
        if (code === 'demographic_required') {
          navigate('/demographics');
          return;
        }
        setError('Failed to start quiz');
      } catch (e) {
        setError(e.message);
      }
    }
    start();
  }, [navigate, i18n.language, session, apiBase]);

  if (error) return <div className="p-4 text-center text-red-600">{error}</div>;
  return <div className="p-4 text-center">Loading...</div>;
}
