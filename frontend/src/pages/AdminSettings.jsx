import React, { useEffect, useState, useCallback } from 'react';
// Layout is provided by AdminLayout.
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function AdminSettings() {
  const { user } = useAuth();
  if (!user || !user.is_admin) {
    return <div className="p-4 text-center">Admin access required</div>;
  }
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const [maxFreeAttempts, setMaxFreeAttempts] = useState('');
  const [msg, setMsg] = useState('');

  const fetchSetting = useCallback(async () => {
    try {
      const authToken = localStorage.getItem('authToken');
      const headers = authToken ? { Authorization: `Bearer ${authToken}` } : {};
      const res = await fetch(`${apiBase}/settings/max_free_attempts`, {
        headers,
      });
      if (res.ok) {
        const data = await res.json();
        setMaxFreeAttempts(data.value ?? '');
      }
    } catch (e) {
      console.error(e);
    }
  }, [apiBase]);

  useEffect(() => { fetchSetting(); }, [fetchSetting]);

  const save = async () => {
    setMsg('');
    const authToken = localStorage.getItem('authToken');
    const headers = authToken
      ? { 'Content-Type': 'application/json', Authorization: `Bearer ${authToken}` }
      : { 'Content-Type': 'application/json' };
    const res = await fetch(`${apiBase}/settings/update`, {
      method: 'POST',
      headers,
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
    );
  }
