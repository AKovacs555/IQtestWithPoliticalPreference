import React, { useState } from 'react';
import Layout from '../components/Layout';
import countryList from '../lib/countryList';

export default function SelectNationality() {
  const [country, setCountry] = useState('');
  const apiBase = import.meta.env.VITE_API_BASE;
  const userId = localStorage.getItem('user_id') || 'demo';

  const save = async () => {
    if (!country) return;
    await fetch(`${apiBase}/user/nationality`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, nationality: country })
    });
    alert('Saved');
  };

  return (
    <Layout>
      <div className="space-y-4 max-w-md mx-auto">
        <select value={country} onChange={e => setCountry(e.target.value)} className="select select-bordered w-full">
          <option value="" disabled>Select country</option>
          {countryList.map(c => (
            <option key={c.code} value={c.code}>{c.name}</option>
          ))}
        </select>
        <button className="btn" onClick={save}>Save</button>
      </div>
    </Layout>
  );
}
