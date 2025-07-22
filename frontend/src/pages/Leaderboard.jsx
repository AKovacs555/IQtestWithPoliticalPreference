import React, { useEffect, useState, useRef } from 'react';
import Layout from '../components/Layout';
import { Chart } from 'chart.js/auto';

export default function Leaderboard() {
  const [data, setData] = useState([]);
  const [partyNames, setPartyNames] = useState({});
  const chartRef = useRef();

  useEffect(() => {
    fetch('/leaderboard')
      .then(res => res.json())
      .then(res => setData(res.leaderboard || []));
    fetch('/survey/start')
      .then(res => res.json())
      .then(res => {
        const map = {};
        res.parties.forEach(p => { map[p.id] = p.name; });
        setPartyNames(map);
      });
  }, []);

  useEffect(() => {
    if (!data.length || !Object.keys(partyNames).length) return;
    const ctx = chartRef.current.getContext('2d');
    const labels = data.map(r => partyNames[r.party_id] || `Party ${r.party_id}`);
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          data: data.map(r => r.avg_iq),
          backgroundColor: 'rgb(75,192,192)'
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }, [data, partyNames]);

  return (
    <Layout>
      <div className="max-w-xl mx-auto py-8 space-y-4">
        <h2 className="text-2xl font-bold text-center">Leaderboard</h2>
        {data.length ? (
          <div className="h-64 overflow-x-auto">
            <canvas ref={chartRef} />
          </div>
        ) : (
          <p className="text-center">Not enough data</p>
        )}
      </div>
    </Layout>
  );
}
