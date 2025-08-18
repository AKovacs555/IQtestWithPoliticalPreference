import React, { useEffect, useState } from 'react';
import { useSession } from '../hooks/useSession';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';

const KEYS = [
  'signup_reward_points',
  'invite_reward_points',
  'daily_reward_points',
  'ad_reward_points',
  'attempt_cost_points'
];

export default function AdminPointsSettings() {
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const { session } = useSession();
  const [values, setValues] = useState({
    signup_reward_points: 0,
    invite_reward_points: 0,
    daily_reward_points: 0,
    ad_reward_points: 0,
    attempt_cost_points: 0
  });
  const [msg, setMsg] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const token = session?.access_token;
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const res = await fetch(`${apiBase}/admin/points/config`, { headers });
        if (res.ok) {
          const data = await res.json();
          setValues(v => ({ ...v, ...data }));
        }
      } catch {}
    };
    load();
  }, [apiBase, session]);

  const save = async () => {
    setMsg('');
    const token = session?.access_token;
    const headers = token
      ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
      : { 'Content-Type': 'application/json' };
    try {
      const body = {};
      KEYS.forEach(k => (body[k] = parseInt(String(values[k] || 0), 10)));
      const res = await fetch(`${apiBase}/admin/points/config`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(body)
      });
      if (!res.ok) throw new Error();
      setMsg('Saved');
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
            {KEYS.map(k => (
              <label key={k} className="block">
                <span>{k}</span>
                <input
                  type="number"
                  className="input input-bordered w-full"
                  value={values[k]}
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

