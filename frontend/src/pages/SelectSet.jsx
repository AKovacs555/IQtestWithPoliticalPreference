import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';

export default function SelectSet() {
  const [sets, setSets] = useState([]);
  useEffect(() => {
    fetch('/quiz/sets')
      .then(res => res.json())
      .then(data => setSets(data.sets || []));
  }, []);

  return (
    <Layout>
      <div className="p-4 space-y-4 max-w-md mx-auto">
        <h2 className="text-xl font-bold text-center">Choose a Test</h2>
        <ul className="space-y-2">
          {sets.map(id => (
            <li key={id} className="card bg-base-100 shadow p-4 flex justify-between items-center">
              <span>{id}</span>
              <Link to={`/start?set=${id}`} className="btn btn-primary btn-sm">Start</Link>
            </li>
          ))}
        </ul>
      </div>
    </Layout>
  );
}
