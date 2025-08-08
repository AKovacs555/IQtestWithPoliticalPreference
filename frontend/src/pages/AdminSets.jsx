import React, { useEffect, useState } from 'react';
// Layout is provided by AdminLayout.
import { useTranslation } from 'react-i18next';

const API_BASE = import.meta.env.VITE_API_BASE || '';
const GITHUB_TOKEN = import.meta.env.VITE_GITHUB_TOKEN;
const GITHUB_OWNER = import.meta.env.VITE_GITHUB_OWNER;
const GITHUB_REPO = import.meta.env.VITE_GITHUB_REPO;

export default function AdminSets() {
  const { t } = useTranslation();
  const [sets, setSets] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/quiz/sets`)
      .then(res => res.json())
      .then(d => setSets(d.sets || []));
  }, []);

  const upload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!GITHUB_TOKEN || !GITHUB_OWNER || !GITHUB_REPO) {
      alert(t('admin_sets.missing_token'));
      return;
    }
    const content = await file.text();
    const encoded = btoa(unescape(encodeURIComponent(content)));
    const path = `questions/${file.name}`;
    const res = await fetch(`https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${path}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${GITHUB_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: `add ${file.name}`, content: encoded })
    });
    if (res.ok) {
      alert(t('admin_sets.uploaded'));
      setSets(s => Array.from(new Set([...s, file.name.replace('.json','')])));
    } else {
      alert(await res.text());
    }
  };

    return (
      <div className="p-4 space-y-4 max-w-md mx-auto">
          <h2 className="text-xl font-bold">{t('admin_sets.title')}</h2>
          <ul className="list-disc pl-5">
            {sets.map(s => <li key={s}>{s}</li>)}
          </ul>
          <div>
            <label className="block mb-2">{t('admin_sets.upload')}</label>
            <input type="file" accept="application/json" onChange={upload} />
          </div>
          <p className="text-sm text-gray-600">{t('admin_sets.note')}</p>
        </div>
    );
  }
