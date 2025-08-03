import React, { useEffect, useRef, useState } from 'react';
import Layout from '../components/Layout';
import { Chart } from 'chart.js/auto';
import { useTranslation } from 'react-i18next';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function Dashboard() {
  const [hist, setHist] = useState([]);
  const [party, setParty] = useState([]);
  const [percentile, setPercentile] = useState(null);
  const [userScore, setUserScore] = useState(null);
  const [partyNames, setPartyNames] = useState({});
  const histRef = useRef();
  const partyRef = useRef();
  const { t } = useTranslation();
  const userId = localStorage.getItem('user_id') || 'demo';

  useEffect(() => {
    fetch(`${API_BASE}/stats/distribution?user_id=${userId}`)
      .then(r => r.json())
      .then(d => {
        setHist(d.histogram || []);
        setPercentile(d.percentile);
        setUserScore(d.user_score);
        setParty(d.party_means || []);
      });
    fetch(`${API_BASE}/survey/start`).then(r => r.json()).then(res => {
      const map = {};
      (res.parties || []).forEach(p => { map[p.id] = p.name; });
      setPartyNames(map);
    });
  }, []);

  useEffect(() => {
    if (!hist.length) return;
    const ctx = histRef.current.getContext('2d');
    const labels = hist.map(h => `${h.bin}-${h.bin + 5}`);
    const colors = hist.map(h => (userScore >= h.bin && userScore < h.bin + 5 ? 'rgb(255,99,132)' : 'rgb(75,192,192)'));
    new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ data: hist.map(h => h.count), backgroundColor: colors }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }, [hist, userScore]);

  useEffect(() => {
    if (!party.length || !Object.keys(partyNames).length) return;
    const ctx = partyRef.current.getContext('2d');
    const labels = party.map(p => partyNames[p.party_id] || `Party ${p.party_id}`);
    new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ data: party.map(p => p.avg_iq), backgroundColor: 'rgb(75,192,192)' }] },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }, [party, partyNames]);

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-4 py-4">
        <h2 className="text-2xl font-bold text-center">{t('dashboard.title')}</h2>
        {userScore == null ? (
          <p className="text-center">{t('dashboard.no_data')}</p>
        ) : (
          <>
            {hist.length ? (
              <div className="h-64"><canvas ref={histRef}></canvas></div>
            ) : null}
            {percentile != null && (
              <p className="text-center">{t('dashboard.percentile', { pct: percentile.toFixed(1) })}</p>
            )}
            {party.length ? (
              <div className="h-64"><canvas ref={partyRef}></canvas></div>
            ) : null}
          </>
        )}
      </div>
    </Layout>
  );
}
