import React, { useEffect, useState, useCallback } from 'react';
import Layout from '../components/Layout';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function AdminSettings() {
  const { user } = useAuth();
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const [maxFreeAttempts, setMaxFreeAttempts] = useState('');
  const [msg, setMsg] = useState('');

  const fetchSetting = useCallback(async () => {
    if (!user) return;
    try {
      const res = await fetch(`${apiBase}/settings/max_free_attempts`, {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMaxFreeAttempts(data.value ?? '');
      }
    } catch (e) {
      console.error(e);
    }
  }, [user, apiBase]);

  useEffect(() => { fetchSetting(); }, [fetchSetting]);

  if (!user?.is_admin) {
    return (
      <Layout>
        <p className="p-4">Admin access required</p>
      </Layout>
    );
  }

  const save = async () => {
    if (!user) return;
    setMsg('');
    const res = await fetch(`${apiBase}/settings/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${user.token}`
      },
      body: JSON.stringify({ key: 'max_free_attempts', value: parseInt(maxFreeAttempts) })
    });
    if (res.ok) {
      setMsg('Saved');
      fetchSetting();
    } else {
      setMsg('Error');
    }
  };

  return (
    <Layout>
      <div className="max-w-xl mx-auto space-y-4">
        <nav className="tabs">
          <Link to="/admin/questions" className="tab tab-bordered">Questions</Link>
          <Link to="/admin/surveys" className="tab tab-bordered">Surveys</Link>
          <Link to="/admin/users" className="tab tab-bordered">Users</Link>
          <Link to="/admin/settings" className="tab tab-bordered tab-active">Settings</Link>
        </nav>
        <div className="space-y-2">
          <label className="block">
            <span>Max free attempts</span>
            <input
              type="number"
              className="input input-bordered w-full"
              value={maxFreeAttempts}
              onChange={e => setMaxFreeAttempts(e.target.value)}
            />
          </label>
          <button className="btn" onClick={save}>Save</button>
          {msg && <div className="text-sm">{msg}</div>}
        </div>
      </div>
    </Layout>
  );
}
