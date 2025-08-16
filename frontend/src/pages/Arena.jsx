import React, { useEffect, useRef, useState } from 'react';
import AppShell from '../components/AppShell';
import { Chart } from 'chart.js/auto';
import { useTranslation } from 'react-i18next';

export default function Arena() {
  const { t } = useTranslation();
  const [stats, setStats] = useState([]);
  const chartRef = useRef();
  const apiBase = import.meta.env.VITE_API_BASE || '';

  useEffect(() => {
    fetch(`${apiBase}/arena/iq_stats`)
      .then((r) => r.json())
      .then(setStats)
      .catch(() => setStats([]));
  }, [apiBase]);

  useEffect(() => {
    if (!stats.length) return;
    const ctx = chartRef.current.getContext('2d');
    const labels = stats.map((s) => s.group_id || s.survey_item_id || '');
    const data = stats.map((s) => s.avg_iq);
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: t('arena.avg_iq', { defaultValue: '平均IQ' }),
            data,
            backgroundColor: 'rgba(59,130,246,0.5)',
          },
        ],
      },
      options: { responsive: true, maintainAspectRatio: false },
    });
  }, [stats, t]);

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto p-4 space-y-4">
        <h2 className="text-2xl font-bold text-center">
          {t('arena.title', { defaultValue: 'IQアリーナ' })}
        </h2>
        <div className="h-64">
          <canvas ref={chartRef}></canvas>
        </div>
      </div>
    </AppShell>
  );
}
