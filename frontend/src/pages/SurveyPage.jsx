import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import LanguageSelector from '../components/LanguageSelector';
import { getSurvey, submitSurvey, completeSurvey } from '../api';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export default function SurveyPage() {
  const [items, setItems] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    const nat = localStorage.getItem('nationality');
    if (!nat) {
      navigate('/select-nationality');
      return;
    }
    if (localStorage.getItem('survey_completed') === 'true') {
      navigate('/test');
      return;
    }
    const uid = localStorage.getItem('user_id');
    getSurvey(i18n.language, uid, nat)
      .then(d => {
        const list = d.items || [];
        if (!list.length) {
          localStorage.setItem('survey_completed', 'true');
          navigate('/test');
          return;
        }
        setItems(list);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [i18n.language, navigate]);

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
      const uid = localStorage.getItem('user_id');
      await submitSurvey(formatted, uid);
      if (uid) {
        await completeSurvey(uid);
        localStorage.setItem('survey_completed', 'true');
      }
      navigate('/test');
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <Layout>
      <div className="space-y-4 max-w-xl mx-auto">
        <LanguageSelector />
        <h2 className="text-2xl font-bold text-center">{t('survey.title')}</h2>
        {loading && <p>{t('survey.loading')}</p>}
        {error && <p className="text-red-600">{error}</p>}
        {!loading && items.map(item => (
          <div key={item.id} className="p-4 bg-surface rounded-md shadow space-y-2">
            <p>{item.statement}</p>
            <div className="flex flex-col space-y-1">
              {item.options.map((opt, idx) => {
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
    </Layout>
  );
}
