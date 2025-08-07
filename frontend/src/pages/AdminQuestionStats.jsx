import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
// import useAuth from '../hooks/useAuth';

export default function AdminQuestionStats() {
  // const { user } = useAuth();
  // if (!user || !user.is_admin) {
  //   return <div>Admin access required</div>;
  // }
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const numQuestions = Number(import.meta.env.VITE_NUM_QUESTIONS || 20);
  const required = {
    easy: Math.ceil(numQuestions * 0.3),
    medium: Math.ceil(numQuestions * 0.4),
    hard: Math.ceil(numQuestions * 0.3),
  };
  const [stats, setStats] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    const authToken = localStorage.getItem('authToken');
    const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {};
    fetch(`${apiBase}/admin/questions/stats`, { headers })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch');
        return res.json();
      })
      .then((data) => setStats(data))
      .catch((err) => setError(err.message));
  }, [apiBase]);

  const languages = Object.keys(stats).sort();

  return (
    <Layout>
      <div className="space-y-4 max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold">Question Stats</h1>
        <p>
          Based on {numQuestions} questions and difficulty ratios (0.3 easy / 0.4 medium / 0.3 hard), each language should have at
          least {required.easy} easy, {required.medium} medium and {required.hard} hard approved questions. Insufficient
          categories are highlighted.
        </p>
        {error && <p className="text-red-600">{error}</p>}
        <table className="min-w-full border">
          <thead>
            <tr>
              <th className="border px-2 py-1">Language</th>
              <th className="border px-2 py-1">Total Approved</th>
              <th className="border px-2 py-1">Easy</th>
              <th className="border px-2 py-1">Medium</th>
              <th className="border px-2 py-1">Hard</th>
              <th className="border px-2 py-1">Sufficient?</th>
            </tr>
          </thead>
          <tbody>
            {languages.map((lang) => {
              const row = stats[lang];
              const ok = row.sufficient.easy && row.sufficient.medium && row.sufficient.hard;
              return (
                <tr key={lang}>
                  <td className="border px-2 py-1">{lang}</td>
                  <td className="border px-2 py-1">{row.total}</td>
                  <td className={`border px-2 py-1 ${row.sufficient.easy ? '' : 'bg-red-200'}`}>{row.easy}</td>
                  <td className={`border px-2 py-1 ${row.sufficient.medium ? '' : 'bg-red-200'}`}>{row.medium}</td>
                  <td className={`border px-2 py-1 ${row.sufficient.hard ? '' : 'bg-red-200'}`}>{row.hard}</td>
                  <td className="border px-2 py-1">{ok ? 'Yes' : 'No'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
