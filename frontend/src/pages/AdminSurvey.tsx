import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';

export default function AdminSurvey() {
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [items, setItems] = useState<any[]>([]);
  const [newStatement, setNewStatement] = useState('');
  const apiBase = import.meta.env.VITE_API_BASE || '';

  const load = async () => {
    if (!token) return;
    const res = await fetch(`${apiBase}/admin/surveys`, {
      headers: { 'X-Admin-Api-Key': token }
    });
    if (res.ok) {
      const data = await res.json();
      setItems(data.questions || []);
    }
  };

  useEffect(() => { load(); }, [token]);

  const create = async () => {
    if (!newStatement) return;
    await fetch(`${apiBase}/admin/surveys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify({ statement: newStatement })
    });
    setNewStatement('');
    load();
  };

  const update = async (id: number, statement: string) => {
    await fetch(`${apiBase}/admin/surveys/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify({ statement })
    });
    load();
  };

  const remove = async (id: number) => {
    if (!confirm('Delete?')) return;
    await fetch(`${apiBase}/admin/surveys/${id}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Api-Key': token }
    });
    load();
  };

  return (
    <Layout>
      <div className="max-w-xl mx-auto space-y-4">
        <nav className="tabs">
          <a href="/admin/questions" className="tab tab-bordered">Questions</a>
          <a className="tab tab-bordered tab-active">Surveys</a>
          <a href="/admin/users" className="tab tab-bordered">Users</a>
        </nav>
        <input
          value={token}
          onChange={e => { setToken(e.target.value); localStorage.setItem('adminToken', e.target.value); }}
          placeholder="API key"
          className="input input-bordered w-full"
        />
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
