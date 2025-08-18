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
        const res = await getQuizStart(i18n.language);
        navigate(`/quiz/play?attempt_id=${res.attempt_id}`);
      } catch (e) {
        setError(e.message);
      }
    }
    start();
  }, [navigate, i18n.language]);

  if (error) return <div>{error}</div>;
  return <div>Loading...</div>;
}
