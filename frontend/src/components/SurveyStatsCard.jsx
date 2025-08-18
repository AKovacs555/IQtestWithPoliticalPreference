import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function SurveyStatsCard({ surveyId, surveyTitle, data }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data?.length) return;
    const labels = data.map((d) => d.option_text);
    const values = data.map((d) => d.avg_iq ?? 0);
    const ctx = canvasRef.current.getContext('2d');
    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: '平均IQ',
            data: values,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, title: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    });
    return () => chart.destroy();
  }, [data]);

  return (
    <div className="min-w-[320px] max-w-[480px] shrink-0 p-4 rounded-xl bg-white/5">
      <div className="mb-2 font-semibold">{surveyTitle}</div>
      <canvas ref={canvasRef} height="200" />
    </div>
  );
}
