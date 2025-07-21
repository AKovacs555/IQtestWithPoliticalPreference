import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';

export default function Leaderboard() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch('/leaderboard')
      .then(res => res.json())
      .then(res => setData(res.leaderboard || []));
  }, []);

  return (
    <Layout>
      <div className="max-w-xl mx-auto py-8 space-y-4">
        <h2 className="text-2xl font-bold text-center">Leaderboard</h2>
        <ul className="space-y-2">
          {data.map(row => (
            <li key={row.party_id} className="flex justify-between bg-base-100 shadow p-2 rounded">
              <span>Party {row.party_id}</span>
              <span className="font-mono">{row.avg_iq.toFixed(1)}</span>
            </li>
          ))}
        </ul>
      </div>
    </Layout>
  );
}
