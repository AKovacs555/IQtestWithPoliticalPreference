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
  const titleString = state?.title || t('survey.title', { defaultValue: 'Survey' });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('sid');
    if (!items.length && sid) {
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
    <div className="max-w-4xl mx-auto px-4 md:px-8 py-6 md:py-10 space-y-6">
      <div className="gold-ring glass-surface wave-sheen p-4 sm:p-5 md:p-6" data-b-spec="survey-panel">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-emerald-300">🧠</span>
            <h2 className="text-[18px] sm:text-[20px] font-extrabold tracking-tight" data-b-spec="survey-title">
              {titleString}
            </h2>
          </div>
        </div>
        {items.map(item => (
          <div key={item.id} className="space-y-4">
            <div className="gold-ring glass-surface p-4 md:p-5">
              <p className="text-base sm:text-lg font-semibold">{item.body || item.statement}</p>
            </div>
            <div className="space-y-3 md:space-y-4">
              {(item.choices || item.options || []).map((option, idx) => {
                const isSelected = answers[item.id] === idx;
                return (
                  <button
                    type="button"
                    key={idx}
                    className={"choice " + (isSelected ? "choice--active" : "")}
                    onClick={() => handleChange(item.id, idx)}
                    data-b-spec="survey-option"
                  >
                    <span className="choice__radio" />
                    <span className="text-[15px] sm:text-base leading-6">{option}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
        {items.length > 0 && (
          <div className="pt-4">
            <button onClick={handleSubmit} className="btn-cta w-full md:w-auto">
              {user?.survey_completed
                ? t('survey.next', { defaultValue: '次へ' })
                : t('survey.submit', { defaultValue: '次へ' })}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

