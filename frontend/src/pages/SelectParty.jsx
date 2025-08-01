import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';

export default function SelectParty() {
  const [parties, setParties] = useState([]);
  const [selected, setSelected] = useState([]);
  const apiBase = import.meta.env.VITE_API_BASE;
  const userId = localStorage.getItem('user_id') || 'demo';
  const nationality = localStorage.getItem('nationality') || 'US';

  useEffect(() => {
    fetch(`${apiBase}/user/parties/${nationality}`)
      .then(r => r.json())
      .then(d => setParties(d.parties || []));
  }, []);

  const toggle = (id) => {
    setSelected(s => s.includes(id) ? s.filter(i => i!==id) : [...s, id]);
  };

  const save = async () => {
    await fetch(`${apiBase}/user/party`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, party_ids: selected })
    });
    alert('Saved');
  };

  return (
    <Layout>
      <div className="space-y-2 max-w-md mx-auto">
        {parties.map(p => (
          <label key={p.id} className="flex items-center space-x-2">
            <input type="checkbox" checked={selected.includes(p.id)} onChange={() => toggle(p.id)} />
            <span>{p.name}</span>
          </label>
        ))}
        <button className="btn" onClick={save}>Save</button>
      </div>
    </Layout>
  );
}
