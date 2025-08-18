import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import { formatIQ } from '../utils/num';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function Leaderboard() {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    fetch(`${API_BASE}/leaderboard?limit=100`)
      .then((r) => r.json())
      .then((d) => setRows(d.items || []));
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
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.user_id}>
                    <td>{r.rank}</td>
                    <td>{r.display_name}</td>
                    <td>{formatIQ(r.best_iq)}</td>
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
