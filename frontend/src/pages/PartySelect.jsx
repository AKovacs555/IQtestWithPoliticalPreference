import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function PartySelect() {
  const [parties, setParties] = useState([]);
  const [selected, setSelected] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API_BASE}/survey/start`)
      .then(res => res.json())
      .then(data => setParties(data.parties || []));
  }, []);

  const toggle = (id) => {
    if (id === 12) {
      setSelected(sel => sel.includes(12) ? [] : [12]);
      return;
    }
    setSelected(sel => {
      const next = sel.includes(id) ? sel.filter(p => p !== id) : [...sel.filter(p => p !== 12), id];
      return next;
    });
  };

  const save = () => {
    const user = localStorage.getItem('user_id') || 'testuser';
    fetch(`${API_BASE}/user/party`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user, party_ids: selected })
    })
      .then(res => {
        if (!res.ok) return res.json().then(d => Promise.reject(d.detail));
      })
      .then(() => navigate('/'))
      .catch(err => alert(err));
  };

  return (
    <Layout>
      <div className="p-4 space-y-4 max-w-md mx-auto">
        <h2 className="text-xl font-bold text-center">Select Party</h2>
        <div className="space-y-2">
          {parties.map(p => (
            <label key={p.id} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selected.includes(p.id)}
                onChange={() => toggle(p.id)}
                className="checkbox"
              />
              <span>{p.name}</span>
            </label>
          ))}
        </div>
        <button onClick={save} className="btn btn-primary w-full">Save</button>
      </div>
    </Layout>
  );
}
