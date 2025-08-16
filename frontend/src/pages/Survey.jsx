import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSession } from '../hooks/useSession';
import { useTranslation } from 'react-i18next';

export default function Survey() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { user, session } = useSession();
  const { t, i18n } = useTranslation();
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const [answers, setAnswers] = useState({});
  const [items, setItems] = useState(state?.items || []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('sid');
    if (!items.length && sid) {
      // Fetch survey when navigated directly
      fetch(`${apiBase}/survey/start?sid=${sid}&lang=${i18n.language}`, {
        headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
      })
        .then(res => res.json())
        .then(data => {
          setItems(data.items || []);
        })
        .catch(() => {});
    }
  }, [apiBase, i18n.language, items.length, session]);

  const handleChange = (itemId, value) => {
    setAnswers(prev => ({ ...prev, [itemId]: value }));
  };

  const handleSubmit = async () => {
    if (!user) return;
    try {
      if (!user.survey_completed) {
        await fetch(`${apiBase}/survey/submit`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            answers: Object.entries(answers).map(([id, idx]) => ({ id, selections: [Number(idx)] })),
          }),
        });
      } else {
        const [itemId, choice] = Object.entries(answers)[0];
        await fetch(`${apiBase}/daily/answer`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ question_id: itemId, answer: { choice: Number(choice) } }),
        });
      }
      navigate('/');
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="survey-container p-4 space-y-4">
      <h1>{t('survey.title', { defaultValue: 'Survey' })}</h1>
      {items.map(item => (
        <div key={item.id} className="survey-item space-y-2">
          <p>{item.body || item.statement}</p>
          {(item.choices || item.options || []).map((option, idx) => (
            <label key={idx} className="block">
              <input
                type="radio"
                name={`q-${item.id}`}
                value={idx}
                onChange={() => handleChange(item.id, idx)}
              />
              <span className="ml-2">{option}</span>
            </label>
          ))}
        </div>
      ))}
      {items.length > 0 && (
        <button onClick={handleSubmit} className="px-4 py-2 bg-blue-600 text-white rounded">
          {user?.survey_completed
            ? t('survey.next', { defaultValue: '回答する' })
            : t('survey.submit', { defaultValue: '送信' })}
        </button>
      )}
    </div>
  );
}
