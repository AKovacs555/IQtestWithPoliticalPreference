import React from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getAttemptQuestions, submitQuiz } from '../api';

export default function QuizPlay() {
  const [items, setItems] = React.useState([]);
  const [answers, setAnswers] = React.useState([]);
  const [current, setCurrent] = React.useState(0);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const attemptId = params.get('attempt_id');

  React.useEffect(() => {
    if (!attemptId) {
      navigate('/');
      return;
    }
    async function load() {
      try {
        const res = await getAttemptQuestions(attemptId);
        setItems(res.items);
        setAnswers(new Array(res.items.length).fill(null));
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [attemptId, navigate]);

  const answer = async (idx) => {
    const a = [...answers];
    a[current] = idx;
    setAnswers(a);
    if (current + 1 < items.length) {
      setCurrent(current + 1);
    } else {
      try {
        await submitQuiz(
          attemptId,
          a.map((ans, i) => ({ id: items[i].id, answer: ans ?? -1 }))
        );
        navigate('/result');
      } catch (e) {
        setError(e.message);
      }
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;
  const q = items[current];
  if (!q) return <div>No questions</div>;
  return (
    <div>
      <div>{q.question}</div>
      <div>
        {q.options.map((opt, i) => (
          <button key={i} onClick={() => answer(i)} style={{ display: 'block', margin: '8px 0' }}>
            {opt}
          </button>
        ))}
      </div>
    </div>
  );
}
