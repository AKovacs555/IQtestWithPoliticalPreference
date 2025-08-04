import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function SelectSet() {
  const [sets, setSets] = useState([]);
  useEffect(() => {
    fetch(`${API_BASE}/quiz/sets`)
      .then(res => res.json())
      .then(data => setSets(data.sets || []));
  }, []);

  return (
    <Layout>
      <div className="p-4 space-y-4 max-w-md mx-auto text-gray-900 dark:text-slate-100">
        <h2 className="text-xl font-bold text-center">Choose a Test</h2>
        <ul className="space-y-2">
          {sets.map(id => (
            <li key={id} className="p-4 bg-white/70 dark:bg-slate-800/60 backdrop-blur-md rounded-md shadow flex justify-between items-center">
              <span>{id}</span>
              <Link
                to={`/start?set=${id}`}
                className="px-4 py-2 rounded-md bg-primary text-white text-sm hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary drop-shadow-md"
              >
                Start
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </Layout>
  );
}
