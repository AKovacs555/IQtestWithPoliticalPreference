import React, { useState } from 'react';
import { useSession } from '../hooks/useSession';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';

export default function AdminPointsGrant() {
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const { session } = useSession();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);
  const [delta, setDelta] = useState(0);
  const [msg, setMsg] = useState('');

  const search = async () => {
    setSelected(null);
    if (!query) return;
    const token = session?.access_token;
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const params = new URLSearchParams({ query, limit: '20', offset: '0' });
    const res = await fetch(`${apiBase}/admin/users/search?${params.toString()}`, {
      headers
    });
    if (res.ok) {
      const data = await res.json();
      setResults(data.users || []);
    } else {
      setResults([]);
    }
  };

  const grant = async () => {
    if (!selected) return;
    const token = session?.access_token;
    const headers = token
      ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
      : { 'Content-Type': 'application/json' };
    setMsg('');
    try {
      const res = await fetch(
        `${apiBase}/admin/users/${selected.hashed_id}/points/add`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({ delta: parseInt(String(delta), 10) })
        }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();
      setSelected({ ...selected, points: data.points });
      setMsg('Saved');
    } catch {
      setMsg('Error');
    }
  };

  return (
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <div className="max-w-xl mx-auto space-y-4">
            <div>
              <input
                className="input input-bordered w-full"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search by email, name or ID"
              />
              <button className="btn btn-sm mt-2" onClick={search}>
                Search
              </button>
            </div>
            {results.length > 0 && (
              <ul className="space-y-2">
                {results.map(u => (
                  <li key={u.hashed_id}>
                    <button
                      className="link"
                      onClick={() => setSelected(u)}
                    >
                      {u.display_name || u.email || u.hashed_id} ({u.points})
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {selected && (
              <div className="space-y-2">
                <div>Current: {selected.points}</div>
                <input
                  type="number"
                  className="input input-bordered w-full"
                  value={delta}
                  onChange={e => setDelta(parseInt(e.target.value, 10))}
                />
                <button className="btn btn-sm" onClick={grant}>
                  Apply
                </button>
              </div>
            )}
            {msg && <div className="text-sm">{msg}</div>}
          </div>
        </div>
      </AdminScaffold>
    </>
  );
}

