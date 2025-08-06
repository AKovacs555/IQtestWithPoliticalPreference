import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { Link } from 'react-router-dom';
import Select from 'react-select';
import getCountryList from '../lib/countryList';
import { useTranslation } from 'react-i18next';
import useAuth from '../hooks/useAuth';

interface SurveyItem {
  group_id: string;
  lang: string;
  statement: string;
  options: string[];
  type: string;
  exclusive_options: number[];
  target_countries?: string[];
}

export default function AdminSurvey() {
  const { user } = useAuth();
  if (!user || !user.is_admin) {
    return <div>Admin access required</div>;
  }
  const [token, setToken] = useState(() => localStorage.getItem('adminToken') || '');
  const [tokenInput, setTokenInput] = useState('');
  const [items, setItems] = useState<SurveyItem[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const { t, i18n } = useTranslation();
  const [countries, setCountries] = useState(() => getCountryList(i18n.language));

  const [newLang, setNewLang] = useState('ja');
  const [newStatement, setNewStatement] = useState('');
  const [newOptions, setNewOptions] = useState('');
  const [newType, setNewType] = useState<'sa' | 'ma'>('sa');
  const [exclusiveOptions, setExclusiveOptions] = useState('');
  const [newTargets, setNewTargets] = useState<string[]>([]);
  const [defaultSurvey, setDefaultSurvey] = useState('');

  const [status, setStatus] = useState<string | null>(null);
  const [editing, setEditing] = useState<any>(null);

  const apiBase = import.meta.env.VITE_API_BASE || '';
  if (!apiBase) {
    console.warn('VITE_API_BASE is not set');
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

  const loadDefault = async () => {
    const res = await fetch(`${apiBase}/admin/dashboard-default-survey`, {
      headers: token ? { 'X-Admin-Api-Key': token } : undefined,
    });
    if (res.ok) {
      const data = await res.json();
      setDefaultSurvey(data.group_id || '');
    }
  };

  useEffect(() => {
    loadLanguages();
    load();
    loadDefault();
  }, [token]);

  useEffect(() => {
    setCountries(getCountryList(i18n.language));
  }, [i18n.language]);

  const create = async () => {
    const exclusiveIndices = exclusiveOptions
      .split(',')
      .map(s => s.trim())
      .filter(s => s !== '')
      .map(s => parseInt(s, 10));

    const payload = {
      lang: newLang,
      statement: newStatement,
      options: newOptions.split('\n').filter(Boolean),
      type: newType,
      exclusive_options: exclusiveIndices,
      target_countries: newTargets,
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
    setExclusiveOptions('');
    setNewTargets([]);
    load();
  };

  const startEdit = (item: SurveyItem) => {
    setEditing({
      group_id: item.group_id,
      lang: item.lang,
      statement: item.statement,
      options: item.options.join('\n'),
      type: item.type,
      exclusive: item.exclusive_options.join(','),
      target_countries: item.target_countries || [],
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
        .filter((v: number) => !isNaN(v)),
      target_countries: editing.target_countries || [],
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

  const saveDefault = async () => {
    const res = await fetch(`${apiBase}/admin/dashboard-default-survey`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Admin-Api-Key': token },
      body: JSON.stringify({ group_id: defaultSurvey }),
    });
    if (res.ok) {
      setStatus(t('saved', { defaultValue: 'Saved' }));
    }
  };

  const remove = async (groupId: string) => {
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
          <Link to="/admin/settings" className="tab tab-bordered">Settings</Link>
        </nav>
        {status && <div className="alert alert-info text-sm">{status}</div>}

        <div className="card card-bordered p-4 space-y-2">
          <h2 className="text-lg font-bold mb-2">New Survey</h2>
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
          <label className="label">
            <span className="label-text">Exclusive option indices (comma-separated)</span>
          </label>
          <input
            value={exclusiveOptions}
            onChange={e => setExclusiveOptions(e.target.value)}
            className="input input-bordered w-full"
            placeholder="e.g. 3 or 0,2"
          />
          <label className="label">
            <span className="label-text">{t('select_target_countries', { defaultValue: 'Select target countries' })}</span>
          </label>
          <Select
            isMulti
            isSearchable
            options={countries.map(c => ({
              value: c.code,
              label: c.name,
            }))}
            value={countries
              .map(c => ({ value: c.code, label: c.name }))
              .filter(o => newTargets.includes(o.value))}
            onChange={vals => setNewTargets(vals.map(v => v.value))}
            placeholder={t('select_target_countries', { defaultValue: 'Select target countries' })}
          />
          <div className="space-x-2 mt-1">
            <button
              className="btn btn-xs"
              onClick={() => setNewTargets(countries.map(c => c.code))}
              type="button"
            >{t('select_all', { defaultValue: 'Select All' })}</button>
            <button
              className="btn btn-xs"
              onClick={() => setNewTargets([])}
              type="button"
            >{t('clear', { defaultValue: 'Clear' })}</button>
          </div>
          <button className="btn" onClick={create}>ADD</button>
        </div>

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
            <label className="label">
              <span className="label-text">{t('select_target_countries', { defaultValue: 'Select target countries' })}</span>
            </label>
            <Select
              isMulti
              isSearchable
              options={countries.map(c => ({
                value: c.code,
                label: c.name,
              }))}
              value={countries
                .map(c => ({ value: c.code, label: c.name }))
                .filter(o => editing.target_countries.includes(o.value))}
              onChange={vals =>
                setEditing({
                  ...editing,
                  target_countries: vals.map(v => v.value),
                })
              }
              placeholder={t('select_target_countries', { defaultValue: 'Select target countries' })}
            />
            <div className="space-x-2 mt-1">
              <button
                className="btn btn-xs"
                onClick={() => setEditing({ ...editing, target_countries: countries.map(c => c.code) })}
                type="button"
              >{t('select_all', { defaultValue: 'Select All' })}</button>
              <button
                className="btn btn-xs"
                onClick={() => setEditing({ ...editing, target_countries: [] })}
                type="button"
              >{t('clear', { defaultValue: 'Clear' })}</button>
            </div>
            <div className="flex space-x-2">
              <button className="btn" onClick={saveEdit}>Save</button>
              <button className="btn" onClick={() => setEditing(null)}>Cancel</button>
            </div>
          </div>
        )}

        <div className="space-y-4">
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

        <div className="card card-bordered p-4 space-y-2 mt-4">
          <h2 className="text-lg font-bold mb-2">{t('select_survey_for_dashboard', { defaultValue: 'Select survey for dashboard' })}</h2>
          <select
            className="select select-bordered w-full"
            value={defaultSurvey}
            onChange={e => setDefaultSurvey(e.target.value)}
          >
            <option value="">--</option>
            {items.map(i => (
              <option key={i.group_id} value={i.group_id}>{i.statement}</option>
            ))}
          </select>
          <button className="btn" onClick={saveDefault}>{t('survey.submit', { defaultValue: 'Submit' })}</button>
        </div>
      </div>
    </Layout>
  );
}

