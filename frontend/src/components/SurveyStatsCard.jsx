import React, { useEffect, useRef } from 'react';
import Chart from 'chart.js/auto';

export default function SurveyStatsCard({ surveyId, surveyTitle, surveyQuestion, data }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data?.length) return;
    const labels = data.map((d) => `${d.option_text} (n=${d.count})`);
    const values = data.map((d) =>
      d.avg_iq !== null && d.avg_iq !== undefined ? Number(d.avg_iq.toFixed(2)) : 0
    );

    const backgroundColors = [
      'rgba(75, 192, 192, 0.7)',
      'rgba(54, 162, 235, 0.7)',
      'rgba(255, 206, 86, 0.7)',
      'rgba(255, 99, 132, 0.7)',
      'rgba(153, 102, 255, 0.7)',
      'rgba(255, 159, 64, 0.7)',
    ];
    const borderColors = backgroundColors.map((c) => c.replace('0.7', '1'));

    const ctx = canvasRef.current.getContext('2d');
    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: '平均IQ',
            data: values,
            backgroundColor: values.map(
              (_, i) => backgroundColors[i % backgroundColors.length]
            ),
            borderColor: values.map((_, i) => borderColors[i % borderColors.length]),
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false }, title: { display: false } },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: '平均IQ' } },
          x: { title: { display: false } },
        },
      },
    });
    return () => chart.destroy();
  }, [data]);

  return (
    <div className="min-w-[320px] max-w-[480px] shrink-0 p-4 rounded-xl bg-white/5">
      <div className="mb-2 font-semibold">
        {surveyTitle}
        {surveyQuestion && (
          <div className="mt-1 text-sm font-normal">{surveyQuestion}</div>
        )}
      </div>
      <canvas ref={canvasRef} height="200" />
    </div>
  );
}
