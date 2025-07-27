import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import Layout from '../components/Layout';

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function History() {
  const { userId } = useParams();
  const [scores, setScores] = useState(null);

  useEffect(() => {
    if (!userId) return;
    fetch(`${API_BASE}/user/history/${userId}`)
      .then(res => res.json())
      .then(data => setScores(data.scores || []));
  }, [userId]);

  if (!userId) {
    return (
      <Layout>
        <div className="p-4 text-center">No user specified.</div>
      </Layout>
    );
  }

  if (!scores) {
    return (
      <Layout>
        <div className="p-4">Loading...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-4 space-y-4 max-w-md mx-auto">
        <h2 className="text-xl font-bold">History</h2>
        <table className="table w-full">
          <thead>
            <tr>
              <th>Date</th>
              <th>Set</th>
              <th>IQ</th>
              <th>%</th>
            </tr>
          </thead>
          <tbody>
            {scores.map((s, i) => (
              <tr key={i}>
                <td>{s.timestamp ? new Date(s.timestamp).toLocaleDateString() : '-'}</td>
                <td>{s.set_id || '-'}</td>
                <td>{s.iq.toFixed(1)}</td>
                <td>{s.percentile.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <Link to={`/settings/${userId}`} className="underline text-sm">Back to Profile</Link>
      </div>
    </Layout>
  );
}
