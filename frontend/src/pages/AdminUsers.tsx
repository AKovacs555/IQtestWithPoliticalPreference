import React, { useEffect, useState } from 'react';
import { useSession } from '../hooks/useSession';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';
// Layout is provided by AdminLayout.

export default function AdminUsers() {
  const [users, setUsers] = useState<any[]>([]);
  const [msg, setMsg] = useState('');
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const { session } = useSession();
  if (!apiBase) {
    console.warn('VITE_API_BASE is not set');
  }

  const load = async () => {
    const token = session?.access_token;
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await fetch(`${apiBase}/admin/users`, { headers });
    if (res.ok) {
      const data = await res.json();
      setUsers(data.users || []);
    } else {
      setUsers([]);
    }
  };

  useEffect(() => {
    load();
  }, [session]);

  const update = async (id: string) => {
    const u = users.find(us => us.hashed_id === id);
    if (!u) return;
    setMsg('');
    try {
      const token = session?.access_token;
      const headers = token
        ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
        : { 'Content-Type': 'application/json' };
      const res = await fetch(`${apiBase}/admin/user/points`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ user_id: id, points: u.points })
      });
      if (!res.ok) throw new Error();
      setMsg('Saved');
    } catch {
      setMsg('Error saving');
    }
  };

  return (
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <div className="max-w-xl mx-auto space-y-4">
            <div className="table-wrap" data-b-spec="admin-table-scroll">
              <table className="table w-full">
                <thead>
                  <tr><th>ID</th><th>Points</th><th></th></tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.hashed_id}>
                      <td className="font-mono">{u.hashed_id}</td>
                      <td>
                        <input
                          type="number"
                          className="input input-bordered w-24"
                          value={u.points ?? 0}
                          onChange={e =>
                            setUsers(us =>
                              us.map(x =>
                                x.hashed_id === u.hashed_id
                                  ? { ...x, points: parseInt(e.target.value, 10) }
                                  : x
                              )
                            )
                          }
                        />
                      </td>
                      <td>
                        <button
                          className="btn btn-sm min-h-[44px] px-4"
                          onClick={() => update(u.hashed_id)}
                          data-b-spec="admin-button-size"
                        >
                          Save
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {msg && <div className="text-sm">{msg}</div>}
          </div>
        </div>
      </AdminScaffold>
    </>
  );
}
