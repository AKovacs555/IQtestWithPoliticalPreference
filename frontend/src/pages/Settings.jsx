import React, { useEffect, useState } from 'react';
import { apiClient } from '../lib/apiClient';
import { Link, useParams } from 'react-router-dom';
import AppShell from '../components/AppShell';

export default function Settings() {
  const { userId } = useParams();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!userId) return;
    apiClient.get(`/user/stats/${userId}`).then(setStats);
  }, [userId]);

  if (!userId) {
    return (
      <AppShell>
        <div className="p-4 text-center">
          <p className="mb-2">No user specified.</p>
          <Link to="/" className="underline">Home</Link>
        </div>
      </AppShell>
    );
  }

  if (!stats) return <AppShell><div className="p-4">Loading...</div></AppShell>;

  return (
    <AppShell>
      <div className="p-4 space-y-2">
        <h2 className="text-xl font-bold mb-2">Your Stats</h2>
        <p>Plays: {stats.plays}</p>
        <p>Referrals: {stats.referrals}</p>
        <p>Points: {stats.points}</p>
        <div>
          <h3 className="font-semibold">Score History</h3>
          <ul className="list-disc list-inside text-sm">
            {stats.scores.map((s, i) => (
              <li key={i}>IQ {s.iq.toFixed(1)} ({s.percentile.toFixed(1)}%)</li>
            ))}
          </ul>
          <Link to={`/history/${userId}`} className="underline text-sm">Full History</Link>
        </div>
        <Link to="/" className="underline">Home</Link>
      </div>
    </AppShell>
  );
}
