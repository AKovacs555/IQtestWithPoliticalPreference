import React, { useEffect, useState, useCallback } from 'react';
import Layout from '../components/Layout';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function AdminSettings() {
  const { user } = useAuth();
  if (!user || !user.is_admin) {
    return <div>Admin access required</div>;
  }
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [tokenInput, setTokenInput] = useState('');
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const [maxFreeAttempts, setMaxFreeAttempts] = useState('');
  const [msg, setMsg] = useState('');

  const fetchSetting = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${apiBase}/settings/max_free_attempts`, {
        headers: { 'X-Admin-Api-Key': token },
      });
      if (res.ok) {
        const data = await res.json();
        setMaxFreeAttempts(data.value ?? '');
      } else if (res.status === 401) {
        setMsg('Invalid admin API key. Please check your settings.');
      }
    } catch (e) {
      console.error(e);
    }
  }, [token, apiBase]);

  useEffect(() => { fetchSetting(); }, [fetchSetting]);

  if (!token) {
    return (
      <Layout>
        <div className="max-w-md mx-auto space-y-4 p-4">
          <h2 className="text-xl font-bold">Admin API key</h2>
          <form
            onSubmit={e => {
              e.preventDefault();
              localStorage.setItem('adminToken', tokenInput);
              setToken(tokenInput);
            }}
            className="space-y-2"
          >
            <input
              value={tokenInput}
              onChange={e => setTokenInput(e.target.value)}
              placeholder="API key"
              className="input input-bordered w-full"
            />
            <button type="submit" className="btn w-full">Save</button>
          </form>
        </div>
      </Layout>
    );
  }

  const save = async () => {
    setMsg('');
    const res = await fetch(`${apiBase}/settings/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Api-Key': token,
      },
      body: JSON.stringify({ key: 'max_free_attempts', value: parseInt(maxFreeAttempts) })
    });
    if (res.status === 401) {
      setMsg('Invalid admin API key. Please check your settings.');
      return;
    }
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
