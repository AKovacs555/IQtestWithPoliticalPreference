import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { Link } from 'react-router-dom';

export default function AdminSurvey() {
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [items, setItems] = useState<any[]>([]);
  const [newStatement, setNewStatement] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const apiBase = import.meta.env.VITE_API_BASE || '';
  if (!apiBase) {
    console.warn('VITE_API_BASE is not set');
  }

  const load = async () => {
    if (!token) return;
    const res = await fetch(`${apiBase}/admin/surveys`, {
      headers: { 'X-Admin-Api-Key': token }
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    if (res.ok) {
      const data = await res.json();
      setItems(data.questions || []);
    }
  };

  useEffect(() => { load(); }, [token]);

  const create = async () => {
    if (!newStatement) return;
    const res = await fetch(`${apiBase}/admin/surveys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify({ statement: newStatement })
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    setNewStatement('');
    load();
  };

  const update = async (id: number, statement: string) => {
    const res = await fetch(`${apiBase}/admin/surveys/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify({ statement })
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    load();
  };

  const remove = async (id: number) => {
    if (!confirm('Delete?')) return;
    const res = await fetch(`${apiBase}/admin/surveys/${id}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Api-Key': token }
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    load();
  };

  return (
    <Layout>
      <div className="max-w-xl mx-auto space-y-4">
        <nav className="tabs">
          <Link to="/admin/questions" className="tab tab-bordered">Questions</Link>
          <Link to="/admin/surveys" className="tab tab-bordered tab-active">Surveys</Link>
          <Link to="/admin/users" className="tab tab-bordered">Users</Link>
        </nav>
        <input
          value={token}
          onChange={e => { setToken(e.target.value); localStorage.setItem('adminToken', e.target.value); }}
          placeholder="API key"
          className="input input-bordered w-full"
        />
        {status && <div className="alert alert-info text-sm">{status}</div>}
        <div className="space-y-2">
          {items.map(item => (
            <div key={item.id} className="flex items-center space-x-2">
              <input
                type="text"
                className="input input-bordered flex-1"
                value={item.statement}
                onChange={e => update(item.id, e.target.value)}
              />
              <button className="btn btn-error btn-xs" onClick={() => remove(item.id)}>Delete</button>
            </div>
          ))}
        </div>
        <div className="flex space-x-2">
          <input
            value={newStatement}
            onChange={e => setNewStatement(e.target.value)}
            className="input input-bordered flex-1"
            placeholder="New statement"
          />
          <button className="btn" onClick={create}>Add</button>
        </div>
      </div>
    </Layout>
  );
}
