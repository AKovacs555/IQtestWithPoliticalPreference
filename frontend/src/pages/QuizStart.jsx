import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getQuizStart } from '../api';

export default function QuizStart() {
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    async function start() {
      try {
        // Start a new quiz attempt
        const res = await getQuizStart(i18n.language);
        // Navigate to the play screen with the attempt ID
        navigate(`/quiz/play?attempt_id=${res.attempt_id}`);
      } catch (e) {
        setError(e.message);
      }
    }
    start();
  }, [navigate, i18n.language]);

  if (error) return <div className="p-4 text-center text-red-600">{error}</div>;
  return <div className="p-4 text-center">Loading...</div>;
}
