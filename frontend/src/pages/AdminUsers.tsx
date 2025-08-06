import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function AdminUsers() {
  const { user } = useAuth();
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [tokenInput, setTokenInput] = useState('');
  const [users, setUsers] = useState<any[]>([]);
  const [msg, setMsg] = useState('');
  const apiBase = import.meta.env.VITE_API_BASE || '';
  if (!apiBase) {
    console.warn('VITE_API_BASE is not set');
  }

  const load = async () => {
    if (!token) return;
    const res = await fetch(`${apiBase}/admin/users`, {
      headers: { 'X-Admin-Api-Key': token }
    });
    if (res.status === 401) {
      setMsg('Invalid admin API key. Please check your settings.');
      setUsers([]);
      return;
    }
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
      const res = await fetch(`${apiBase}/admin/user/free_attempts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
        body: JSON.stringify({ user_id: id, free_attempts: u.free_attempts })
      });
      if (res.status === 401) {
        setMsg('Invalid admin API key. Please check your settings.');
        return;
      }
      if (!res.ok) throw new Error();
      setMsg('Saved');
    } catch {
      setMsg('Error saving');
    }
  };

  if (!user || !user.is_admin) {
    return (
      <Layout>
        <div className="p-4">Admin access required</div>
      </Layout>
    );
  }

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

  return (
    <Layout>
      <div className="max-w-xl mx-auto space-y-4">
        <nav className="tabs">
          <Link to="/admin/questions" className="tab tab-bordered">Questions</Link>
          <Link to="/admin/surveys" className="tab tab-bordered">Surveys</Link>
          <Link to="/admin/users" className="tab tab-bordered tab-active">Users</Link>
          <Link to="/admin/settings" className="tab tab-bordered">Settings</Link>
        </nav>
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
