import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import LanguageSelector from '../components/LanguageSelector';
import { getSurvey, submitSurvey, completeSurvey } from '../api';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../hooks/useSession';

export default function SurveyPage() {
  const [items, setItems] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [surveyTitle, setSurveyTitle] = useState('');
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { userId } = useSession();

  // ---------- helpers: robust field extraction ----------
  const pick = (obj, keys) => {
    if (!obj) return undefined;
    for (const k of keys) if (obj[k]) return obj[k];
    return undefined;
  };
  const prefer = (...vals) => vals.find(v => typeof v === 'string' && v.trim().length) || '';
  const useQS = () => {
    try {
      return new URLSearchParams(window.location.search || '');
    } catch {
      return new URLSearchParams('');
    }
  };
  const qs = useQS();

  useEffect(() => {
    // 前提条件チェック
    const nat = localStorage.getItem('nationality');
    if (!nat) {
      navigate('/select-nationality');
      return;
    }
    const demDone = localStorage.getItem('demographic_completed') === 'true';
    if (!demDone) {
      navigate('/demographics');
      return;
    }
    if (localStorage.getItem('survey_completed') === 'true') {
      navigate('/quiz');
      return;
    }
    const uid = userId;
    getSurvey(i18n.language, uid, nat)
      .then(d => {
        const list = d.items || [];
        // resolve survey title from data or QS
        setSurveyTitle(
          prefer(
            pick(d, ['title', 'name', 'label', 'heading']),
            qs.get('title'),
            ''
          )
        );
        if (!list.length) {
          localStorage.setItem('survey_completed', 'true');
          navigate('/quiz');
          return;
        }
        setItems(list);
      })
      .catch(e => {
        if (e.code === 'nationality_required') {
          navigate('/select-nationality');
          return;
        }
        setError(e.message);
      })
      .finally(() => setLoading(false));
  }, [userId, i18n.language, navigate]);

  const handleChange = (item, optionIdx) => {
    setAnswers(a => {
      const current = a[item.id] || [];
      let updated;
      if (item.type === 'sa') {
        updated = [optionIdx];
      } else {
        // multi-answer
        const isSelected = current.includes(optionIdx);
        if (isSelected) {
          updated = current.filter(i => i !== optionIdx);
        } else {
          const exclusive = item.exclusive_options || [];
          if (exclusive.includes(optionIdx)) {
            updated = [optionIdx];
          } else {
            updated = current.filter(i => !exclusive.includes(i)).concat(optionIdx);
          }
        }
      }
      return { ...a, [item.id]: updated };
    });
  };

  const submit = async () => {
    const formatted = Object.entries(answers).map(([id, sel]) => ({
      id,
      selections: sel.map(Number),
    }));
    try {
      const uid = userId;
      await submitSurvey(formatted, uid);
      if (uid) {
        await completeSurvey(uid);
      }
      localStorage.setItem('survey_completed', 'true');
      const demDone = localStorage.getItem('demographic_completed') === 'true';
      navigate(demDone ? '/quiz' : '/demographics');
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <AppShell>
      <div className="space-y-4 max-w-xl mx-auto">
        <LanguageSelector />
        <h2 className="text-2xl font-bold text-center" data-b-spec="survey-title">{surveyTitle || t('survey.title')}</h2>
        {loading && <p>{t('survey.loading')}</p>}
        {error && <p className="text-red-600">{error}</p>}
        {!loading && items.map(item => (
          <div key={item.id} className="space-y-2">
            {/* Question title/stem */}
            {(() => {
              const q: any = item;
              const stem =
                q.statement ||
                q.title ||
                q.text ||
                q.prompt ||
                q.question ||
                q.content ||
                q.label ||
                (typeof q === 'string' ? q : '') ||
                '';
              return stem ? (
                <div className="gold-ring glass-surface p-4 md:p-5 mt-3 mb-3" data-b-spec="survey-question-stem">
                  <h3 className="text-base sm:text-lg font-semibold">{stem}</h3>
                </div>
              ) : null;
            })()}
            <div className="flex flex-col space-y-1">
              {item.options?.map((opt, idx) => {
                const selected = answers[item.id] || [];
                const exclusive = item.exclusive_options || [];
                const exclusiveSelected = selected.some(i => exclusive.includes(i));
                const disabled = item.type === 'ma' && exclusiveSelected && !selected.includes(idx);
                const inputType = item.type === 'ma' ? 'checkbox' : 'radio';
                const checked = selected.includes(idx);
                return (
                  <label key={idx} className="flex items-center space-x-2">
                    <input
                      type={inputType}
                      name={`q-${item.id}`}
                      checked={checked}
                      disabled={disabled}
                      onChange={() => handleChange(item, idx)}
                    />
                    <span>{opt}</span>
                  </label>
                );
              })}
            </div>
          </div>
        ))}
        {!loading && items.length > 0 && (
          <button
            className="px-4 py-2 rounded-md bg-primary text-white"
            onClick={submit}
          >
            {t('survey.submit')}
          </button>
        )}
      </div>
    </AppShell>
  );
}
