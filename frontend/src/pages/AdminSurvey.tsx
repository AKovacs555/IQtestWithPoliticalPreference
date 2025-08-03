import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { Link } from 'react-router-dom';

interface SurveyItem {
  group_id: number;
  lang: string;
  statement: string;
  options: string[];
  type: string;
  exclusive_options: number[];
}

export default function AdminSurvey() {
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [items, setItems] = useState<SurveyItem[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);

  const [newLang, setNewLang] = useState('ja');
  const [newStatement, setNewStatement] = useState('');
  const [newOptions, setNewOptions] = useState('');
  const [newType, setNewType] = useState<'sa' | 'ma'>('sa');
  const [newExclusive, setNewExclusive] = useState('3');

  const [status, setStatus] = useState<string | null>(null);
  const [editing, setEditing] = useState<any>(null);

  const apiBase = import.meta.env.VITE_API_BASE || '';
  if (!apiBase) {
    console.warn('VITE_API_BASE is not set');
  }

  const loadLanguages = async () => {
    if (!token) return;
    const res = await fetch(`${apiBase}/admin/surveys/languages`, {
      headers: { 'X-Admin-Api-Key': token }
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    const data = await res.json();
    setLanguages(data.languages || []);
    if (!data.languages?.includes(newLang)) {
      setNewLang(data.languages?.[0] || '');
    }
  };

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

  useEffect(() => {
    loadLanguages();
    load();
  }, [token]);

  const create = async () => {
    const payload = {
      lang: newLang,
      statement: newStatement,
      options: newOptions.split('\n').filter(Boolean),
      type: newType,
      exclusive_options: newExclusive
        .split(',')
        .map(v => Number(v.trim()))
        .filter(v => !isNaN(v))
    };
    const res = await fetch(`${apiBase}/admin/surveys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify(payload)
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    setNewStatement('');
    setNewOptions('');
    load();
  };

  const startEdit = (item: SurveyItem) => {
    setEditing({
      group_id: item.group_id,
      lang: item.lang,
      statement: item.statement,
      options: item.options.join('\n'),
      type: item.type,
      exclusive: item.exclusive_options.join(',')
    });
  };

  const saveEdit = async () => {
    const payload = {
      lang: editing.lang,
      statement: editing.statement,
      options: editing.options.split('\n').filter(Boolean),
      type: editing.type,
      exclusive_options: editing.exclusive
        .split(',')
        .map((v: string) => Number(v.trim()))
        .filter((v: number) => !isNaN(v))
    };
    const res = await fetch(`${apiBase}/admin/surveys/${editing.group_id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify(payload)
    });
    if (res.status === 401) {
      setStatus('Invalid admin API key. Please check your settings.');
      return;
    }
    setEditing(null);
    load();
  };

  const remove = async (groupId: number) => {
    if (!confirm('Delete?')) return;
    const res = await fetch(`${apiBase}/admin/surveys/${groupId}`, {
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
          onChange={e => {
            setToken(e.target.value);
            localStorage.setItem('adminToken', e.target.value);
          }}
          placeholder="API key"
          className="input input-bordered w-full"
        />
        {status && <div className="alert alert-info text-sm">{status}</div>}

        {editing && (
          <div className="p-2 border space-y-2">
            <h3 className="font-bold">Edit</h3>
            <input value={editing.lang} disabled className="input input-bordered w-full" />
            <textarea
              className="textarea textarea-bordered w-full"
              value={editing.statement}
              onChange={e => setEditing({ ...editing, statement: e.target.value })}
            />
            <textarea
              className="textarea textarea-bordered w-full"
              placeholder="Options separated by newline"
              value={editing.options}
              onChange={e => setEditing({ ...editing, options: e.target.value })}
            />
            <div className="flex space-x-2">
              <label><input type="radio" checked={editing.type === 'sa'} onChange={() => setEditing({ ...editing, type: 'sa' })} /> SA</label>
              <label><input type="radio" checked={editing.type === 'ma'} onChange={() => setEditing({ ...editing, type: 'ma' })} /> MA</label>
            </div>
            <input
              className="input input-bordered w-full"
              placeholder="Exclusive option indexes comma separated"
              value={editing.exclusive}
              onChange={e => setEditing({ ...editing, exclusive: e.target.value })}
            />
            <div className="flex space-x-2">
              <button className="btn" onClick={saveEdit}>Save</button>
              <button className="btn" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {items.map(item => (
            <div key={item.group_id} className="flex items-center justify-between space-x-2">
              <span>{item.statement}</span>
              <div className="space-x-2">
                <button className="btn btn-xs" onClick={() => startEdit(item)}>Edit</button>
                <button className="btn btn-error btn-xs" onClick={() => remove(item.group_id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>

        <div className="space-y-2 border p-2">
          <h3 className="font-bold">New Survey</h3>
          <div>
            <label className="block text-sm">Language</label>
            <select
              className="select select-bordered w-full"
              value={newLang}
              onChange={e => setNewLang(e.target.value)}
            >
              {languages.map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <textarea
            className="textarea textarea-bordered w-full"
            placeholder="Statement"
            value={newStatement}
            onChange={e => setNewStatement(e.target.value)}
          />
          <textarea
            className="textarea textarea-bordered w-full"
            placeholder="Options separated by newline"
            value={newOptions}
            onChange={e => setNewOptions(e.target.value)}
          />
          <div className="flex space-x-2">
            <label><input type="radio" checked={newType === 'sa'} onChange={() => setNewType('sa')} /> SA</label>
            <label><input type="radio" checked={newType === 'ma'} onChange={() => setNewType('ma')} /> MA</label>
          </div>
          <input
            className="input input-bordered w-full"
            placeholder="Exclusive option indexes comma separated"
            value={newExclusive}
            onChange={e => setNewExclusive(e.target.value)}
          />
          <button className="btn" onClick={create}>Add</button>
        </div>
      </div>
    </Layout>
  );
}

