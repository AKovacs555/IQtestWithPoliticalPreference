import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';

export default function AdminUsers() {
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [users, setUsers] = useState<any[]>([]);
  const [msg, setMsg] = useState('');
  const apiBase = import.meta.env.VITE_API_BASE || '';

  const load = async () => {
    if (!token) return;
    const res = await fetch(`${apiBase}/admin/users`, {
      headers: { 'X-Admin-Api-Key': token }
    });
    if (res.ok) {
      const data = await res.json();
      setUsers(data.users || []);
    }
  };

  useEffect(() => { load(); }, [token]);

  const update = async (id: string) => {
    const u = users.find(us => us.hashed_id === id);
    if (!u) return;
    setMsg('');
    try {
      const res = await fetch(`${apiBase}/admin/users/free_attempts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
        body: JSON.stringify({ user_id: id, free_attempts: u.free_attempts })
      });
      if (!res.ok) throw new Error();
      setMsg('Saved');
    } catch {
      setMsg('Error saving');
    }
  };

  return (
    <Layout>
      <div className="max-w-xl mx-auto space-y-4">
        <nav className="tabs">
          <a href="/admin/questions" className="tab tab-bordered">Questions</a>
          <a href="/admin/surveys" className="tab tab-bordered">Surveys</a>
          <a className="tab tab-bordered tab-active">Users</a>
        </nav>
        <input
          value={token}
          onChange={e => { setToken(e.target.value); localStorage.setItem('adminToken', e.target.value); }}
          placeholder="API key"
          className="input input-bordered w-full"
        />
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
                    onChange={e => setUsers(us => us.map(x => x.hashed_id === u.hashed_id ? { ...x, free_attempts: parseInt(e.target.value, 10) } : x))}
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
    </Layout>
  );
}
