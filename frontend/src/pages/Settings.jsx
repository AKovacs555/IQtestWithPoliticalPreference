import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import Layout from '../components/Layout';

export default function Settings() {
  const { userId } = useParams();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!userId) return;
    fetch(`/user/stats/${userId}`)
      .then(res => res.json())
      .then(setStats);
  }, [userId]);

  if (!userId) {
    return (
      <Layout>
        <div className="p-4 text-center">
          <p className="mb-2">No user specified.</p>
          <Link to="/" className="underline">Home</Link>
        </div>
      </Layout>
    );
  }

  if (!stats) return <Layout><div className="p-4">Loading...</div></Layout>;

  return (
    <Layout>
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
        <div className="p-4 space-y-2">
        <h2 className="text-xl font-bold mb-2">Your Stats</h2>
        <p>Plays: {stats.plays}</p>
        <p>Referrals: {stats.referrals}</p>
        <div>
          <h3 className="font-semibold">Score History</h3>
          <ul className="list-disc list-inside text-sm">
            {stats.scores.map((s, i) => (
              <li key={i}>IQ {s.iq.toFixed(1)} ({s.percentile.toFixed(1)}%)</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-semibold">Party Changes</h3>
          <ul className="list-disc list-inside text-sm">
            {stats.party_log.map((p, i) => (
              <li key={i}>{p.timestamp}: {p.party_ids.join(', ')}</li>
            ))}
          </ul>
        </div>
          <Link to="/" className="underline">Home</Link>
        </div>
      </motion.div>
    </Layout>
  );
}
