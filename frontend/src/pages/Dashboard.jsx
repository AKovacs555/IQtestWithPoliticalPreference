import React, { useEffect, useRef, useState } from 'react';
import AppShell from '../components/AppShell';
import { Chart } from 'chart.js/auto';
import { useTranslation } from 'react-i18next';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const userId = localStorage.getItem('user_id') || 'demo';
  const histRef = useRef();
  const barRef = useRef();
  const [hist, setHist] = useState({ histogram: [], bucket_edges: [], user_score: null, user_percentile: null });
  const [surveyList, setSurveyList] = useState([]);
  const [selectedSurvey, setSelectedSurvey] = useState('');
  const [optionStats, setOptionStats] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/stats/iq_histogram?user_id=${userId}`)
      .then(r => r.json())
      .then(setHist);

    fetch(`${API_BASE}/surveys?lang=${i18n.language}`)
      .then(r => r.json())
      .then(d => setSurveyList(d.questions || []));

    fetch(`${API_BASE}/admin/dashboard-default-survey`)
      .then(r => r.json())
      .then(d => setSelectedSurvey(d.group_id || ''));
  }, [i18n.language, userId]);

  useEffect(() => {
    if (!hist.histogram.length) return;
    const ctx = histRef.current.getContext('2d');
    const labels = hist.bucket_edges.slice(0, -1).map((b, i) => `${b}-${hist.bucket_edges[i + 1]}`);
    const colors = labels.map((label, idx) => {
      const start = hist.bucket_edges[idx];
      const end = hist.bucket_edges[idx + 1];
      return hist.user_score >= start && hist.user_score < end ? 'rgb(255,99,132)' : 'rgb(75,192,192)';
    });
    new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ data: hist.histogram, backgroundColor: colors }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }, [hist]);

  useEffect(() => {
    if (!selectedSurvey) return;
    fetch(`${API_BASE}/stats/survey_options/${selectedSurvey}`)
      .then(r => r.json())
      .then(d => setOptionStats(d));
  }, [selectedSurvey]);

  useEffect(() => {
    if (!optionStats) return;
    const ctx = barRef.current.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: optionStats.options,
        datasets: [{ data: optionStats.averages, backgroundColor: 'rgb(75,192,192)' }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }, [optionStats]);

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-4 py-4">
        <h2 className="text-2xl font-bold text-center">{t('dashboard.title')}</h2>
        {hist.user_score == null ? (
          <p className="text-center">{t('dashboard.no_data')}</p>
        ) : (
          <>
            {hist.histogram.length ? (
              <div className="h-64"><canvas ref={histRef}></canvas></div>
            ) : null}
            {hist.user_percentile != null && (
              <p className="text-center">{t('dashboard.percentile', { pct: hist.user_percentile.toFixed(1) })}</p>
            )}
            <div>
              <label className="block mb-1">{t('dashboard.select_survey', { defaultValue: 'Select survey' })}</label>
              <select
                className="select select-bordered w-full"
                value={selectedSurvey}
                onChange={e => setSelectedSurvey(e.target.value)}
              >
                <option value="">--</option>
                {surveyList.map(s => (
                  <option key={s.group_id} value={s.group_id}>{s.statement}</option>
                ))}
              </select>
            </div>
            {optionStats && optionStats.options.length ? (
              <div className="h-64"><canvas ref={barRef}></canvas></div>
            ) : null}
          </>
        )}
      </div>
    </AppShell>
  );
}
