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
  const [survey, setSurvey] = useState(state?.survey || null);
  const [items, setItems] = useState(state?.items || []);
  const [selected, setSelected] = useState(new Set());
  const [error, setError] = useState('');

  useEffect(() => {
    const nat = localStorage.getItem('nationality');
    if (!nat) {
      navigate('/select-nationality');
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('sid');
    if ((!items.length || !survey) && sid) {
      fetch(`${apiBase}/survey/start?sid=${sid}&lang=${i18n.language}`, {
        headers: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
      })
        .then(res => res.json())
        .then(data => {
          setSurvey(data.survey);
          setItems(data.items || []);
        })
        .catch(() => {});
    }
  }, [apiBase, i18n.language, items.length, session, survey, navigate]);

  const single = survey?.is_single_choice;

  function toggleChoice(itemId, isExclusive) {
    setSelected(prev => {
      const next = new Set(prev);
      if (single) {
        next.clear();
        next.add(itemId);
        return next;
      }
      if (isExclusive) {
        next.clear();
        next.add(itemId);
        return next;
      }
      if (next.has(itemId)) {
        next.delete(itemId);
      } else {
        next.add(itemId);
      }
      const chosenExclusive = items.find(i => i.is_exclusive && next.has(i.id));
      if (chosenExclusive) return new Set([chosenExclusive.id]);
      return next;
    });
  }

  const handleSubmit = async () => {
    const userId = user?.id ?? null;
    const itemIdList = Array.from(selected);
    const ordered = [...items].sort((a, b) => a.position - b.position);
    const indexSelections = itemIdList
      .map(id => ordered.findIndex(o => o.id === id))
      .filter(idx => idx >= 0);

    const payload = {
      user_id: userId,
      lang: i18n.language,
      survey_id: survey.id,
      survey_group_id: survey.group_id,
      answers: [{ id: survey.id, item_ids: itemIdList, selections: indexSelections }],
    };

    const res = await fetch(`${apiBase}/survey/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const msg = await res.text().catch(() => 'Submit failed');
      setError(msg);
      return;
    }
    localStorage.setItem('survey_completed', 'true');
    navigate('/');
  };

  const titleString =
    survey?.question_text || survey?.title || t('survey.title', { defaultValue: 'Survey' });

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
        {error && <div className="text-red-500 mb-4">{error}</div>}
        {items.map(item => (
          <div key={item.id} className="space-y-4">
            <button
              type="button"
              className={
                'choice w-full text-left ' +
                (selected.has(item.id) ? 'choice--active' : '')
              }
              onClick={() => toggleChoice(item.id, item.is_exclusive)}
              data-b-spec="survey-option"
            >
              <span className="choice__radio" />
              <span className="text-[15px] sm:text-base leading-6">{item.body}</span>
            </button>
          </div>
        ))}
        {items.length > 0 && (
          <div className="pt-4">
            <button
              onClick={handleSubmit}
              className="btn-cta w-full md:w-auto"
              disabled={selected.size === 0}
            >
              {t('survey.submit', { defaultValue: '次へ' })}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}


