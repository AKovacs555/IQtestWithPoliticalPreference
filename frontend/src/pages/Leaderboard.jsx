import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function Leaderboard() {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    fetch(`${API_BASE}/leaderboard?limit=100`)
      .then(r => r.json())
      .then(d => setRows(d.leaderboard || []));
  }, []);
  return (
    <AppShell>
      <div className="max-w-xl mx-auto py-8 space-y-4">
        <h2 className="text-2xl font-bold text-center">Leaderboard</h2>
        <div className="overflow-x-auto">
          {rows.length ? (
            <table className="table w-full">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Name</th>
                  <th>Score</th>
                  <th>Percentile</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, idx) => (
                  <tr key={r.user_id || idx}>
                    <td>{idx + 1}</td>
                    <td>{r.display_name}</td>
                    <td>{r.best_iq}</td>
                    <td>{r.best_percentile}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-center">No data</p>
          )}
        </div>
      </div>
    </AppShell>
  );
}
