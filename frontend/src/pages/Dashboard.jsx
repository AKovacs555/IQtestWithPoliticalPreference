import React, { useEffect, useRef, useState } from 'react';
import AppShell from '../components/AppShell';
import AchievementModal from '../components/AchievementModal';
import { Chart } from 'chart.js/auto';
import { useTranslation } from 'react-i18next';
import { useSession } from '../hooks/useSession';
import { fetchSurveyFeed } from '../api';
import { supabase } from '../lib/supabaseClient';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const { userId, session } = useSession();
  const histRef = useRef();
  const barRef = useRef();
  const [hist, setHist] = useState({ histogram: [], bucket_edges: [], user_score: null, user_percentile: null });
  const [surveyList, setSurveyList] = useState([]);
  const [selectedSurvey, setSelectedSurvey] = useState('');
  const [optionStats, setOptionStats] = useState(null);
  const [inviteCode, setInviteCode] = useState('');
  const [history, setHistory] = useState([]);
  const [tab, setTab] = useState('stats');
  const [achievementsOpen, setAchievementsOpen] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/stats/iq_histogram?user_id=${userId || 'demo'}`)
      .then(r => r.json())
      .then(setHist);

    fetchSurveyFeed(supabase, i18n.language ?? null, 50, 0)
      .then((rows) => setSurveyList(rows))
      .catch(() => setSurveyList([]));

    fetch(`${API_BASE}/admin/dashboard-default-survey`)
      .then(r => r.json())
      .then(d => setSelectedSurvey(d.group_id || ''));

    const token = session?.access_token;
    if (token) {
      fetch(`${API_BASE}/referral/code`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.json())
        .then(d => setInviteCode(d.invite_code || ''));
      fetch(`${API_BASE}/user/history`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.json())
        .then(d => setHistory(d.attempts || []));
    }
  }, [i18n.language, userId, session]);

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
        <div className="text-center">
          <button className="btn btn-secondary btn-sm" onClick={() => setAchievementsOpen(true)}>Achievements</button>
        </div>
        <div className="tabs justify-center">
          <a
            className={`tab tab-bordered ${tab==='stats'?'tab-active':''}`}
            onClick={() => setTab('stats')}
          >
            {t('dashboard.title')}
          </a>
          <a
            className={`tab tab-bordered ${tab==='history'?'tab-active':''}`}
            onClick={() => setTab('history')}
          >
            {t('dashboard.history', {defaultValue:'History'})}
          </a>
        </div>
        {tab === 'stats' ? (
          hist.user_score == null ? (
            <p className="text-center">{t('dashboard.no_data')}</p>
          ) : (
            <>
              {inviteCode && (
                <p className="text-center text-sm">
                  Invite link: {`${window.location.origin}/?r=${inviteCode}`}
                </p>
              )}
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
                  {surveyList.map((s) => (
                    <option key={s.group_id} value={s.group_id}>{s.question_text}</option>
                  ))}
                </select>
              </div>
              {optionStats && optionStats.options.length ? (
                <div className="h-64"><canvas ref={barRef}></canvas></div>
              ) : null}
            </>
          )
        ) : (
          <div className="overflow-x-auto">
            {history.length ? (
              <table className="table w-full">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Set</th>
                    <th>Score</th>
                    <th>Percentile</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h, i) => (
                    <tr key={i}>
                      <td>{h.date}</td>
                      <td>{h.set}</td>
                      <td>{h.score}</td>
                      <td>{h.percentile}</td>
                      <td>{h.duration}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-center">{t('dashboard.no_data')}</p>
            )}
          </div>
        )}
        <AchievementModal isOpen={achievementsOpen} onClose={() => setAchievementsOpen(false)} />
      </div>
    </AppShell>
  );
}
