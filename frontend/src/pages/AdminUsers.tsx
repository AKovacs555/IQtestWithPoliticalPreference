import React, { useEffect, useState } from 'react';
import { useSession } from '../hooks/useSession';
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
      const res = await fetch(`${apiBase}/admin/user/free_attempts`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ user_id: id, free_attempts: u.free_attempts })
      });
      if (!res.ok) throw new Error();
      setMsg('Saved');
    } catch {
      setMsg('Error saving');
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-4">
        <table className="table w-full">
          <thead>
            <tr><th>ID</th><th>Free attempts</th><th></th></tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.hashed_id}>
                <td className="font-mono">{u.hashed_id}</td>
                <td>
                  <input
                    type="number"
                    className="input input-bordered w-24"
                    value={u.free_attempts ?? 0}
                    onChange={e =>
                      setUsers(us =>
                        us.map(x =>
                          x.hashed_id === u.hashed_id
                            ? { ...x, free_attempts: parseInt(e.target.value, 10) }
                            : x
                        )
                      )
                    }
                  />
                </td>
                <td>
                  <button className="btn btn-sm" onClick={() => update(u.hashed_id)}>Save</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {msg && <div className="text-sm">{msg}</div>}
      </div>
    );
}
