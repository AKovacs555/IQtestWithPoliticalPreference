import React, { useEffect, useState, useCallback } from 'react';
import { useSession } from '../hooks/useSession';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';

export default function AdminSettings() {
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const { session } = useSession();
  const [values, setValues] = useState({
    ad_reward_points: '',
    daily_reward_points: '',
    invite_reward_points: '',
    point_cost_per_attempt: ''
  });
  const [msg, setMsg] = useState('');

  const fetchSetting = useCallback(async () => {
    try {
      const token = session?.access_token;
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const keys = Object.keys(values);
      const res = await Promise.all(
        keys.map(k => fetch(`${apiBase}/settings/${k}`, { headers }))
      );
      const data = {};
      for (let i = 0; i < keys.length; i++) {
        if (res[i].ok) {
          const d = await res[i].json();
          data[keys[i]] = d.value ?? '';
        } else {
          data[keys[i]] = '';
        }
      }
      setValues(v => ({ ...v, ...data }));
    } catch (e) {
      console.error(e);
    }
  }, [apiBase, session]);

  useEffect(() => {
    fetchSetting();
  }, [fetchSetting]);

  const save = async () => {
    setMsg('');
    const token = session?.access_token;
    const headers = token
      ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
      : { 'Content-Type': 'application/json' };
    try {
      await Promise.all(
        Object.entries(values).map(([k, v]) =>
          fetch(`${apiBase}/settings/update`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ key: k, value: parseInt(String(v)) })
          })
        )
      );
      setMsg('Saved');
      fetchSetting();
    } catch {
      setMsg('Error');
    }
  };

  const onChange = (key, val) => {
    setValues(v => ({ ...v, [key]: val }));
  };

  return (
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <div className="max-w-xl mx-auto space-y-4">
            {Object.entries(values).map(([k, v]) => (
              <label key={k} className="block">
                <span>{k}</span>
                <input
                  type="number"
                  className="input input-bordered w-full"
                  value={v}
                  onChange={e => onChange(k, e.target.value)}
                />
              </label>
            ))}
            <button className="btn btn-sm min-h-[44px] px-4" onClick={save}>Save</button>
            {msg && <div className="text-sm">{msg}</div>}
          </div>
        </div>
      </AdminScaffold>
    </>
  );
}
