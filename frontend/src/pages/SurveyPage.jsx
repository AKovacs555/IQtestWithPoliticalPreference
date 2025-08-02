import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import LanguageSelector from '../components/LanguageSelector';
import { getSurvey, submitSurvey } from '../api';
import { useTranslation } from 'react-i18next';

export default function SurveyPage() {
  const [items, setItems] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const { t } = useTranslation();

  useEffect(() => {
    getSurvey()
      .then(d => setItems(d.items || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (id, value) => {
    setAnswers(a => ({ ...a, [id]: Number(value) }));
  };

  const submit = async () => {
    const payload = Object.entries(answers).map(([id, value]) => ({ id: Number(id), value }));
    try {
      await submitSurvey(payload);
      setSubmitted(true);
    } catch (e) {
      setError(e.message);
    }
  };

  if (submitted) {
    return (
      <Layout>
        <div className="py-8 text-center">
          <p>{t('survey.thank_you')}</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-4 max-w-xl mx-auto">
        <LanguageSelector />
        <h2 className="text-2xl font-bold text-center">{t('survey.title')}</h2>
        {loading && <p>{t('survey.loading')}</p>}
        {error && <p className="text-error">{error}</p>}
        {!loading && items.map(item => (
          <div key={item.id} className="card bg-base-100 p-4 space-y-2">
            <p>{item.statement}</p>
            {item.type === 'slider' ? (
              <input type="range" min="1" max="5" value={answers[item.id] || 3} onChange={e => handleChange(item.id, e.target.value)} className="range" />
            ) : (
              <div className="flex justify-between">
                {[1,2,3,4,5].map(v => (
                  <label key={v} className="flex flex-col items-center">
                    <input type="radio" name={`q-${item.id}`} value={v} checked={answers[item.id]===v} onChange={() => handleChange(item.id,v)} />
                    <span>{v}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}
        {!loading && items.length > 0 && (
          <button className="btn btn-primary" onClick={submit}>{t('survey.submit')}</button>
        )}
      </div>
    </Layout>
  );
}
