import React, { useState } from 'react';
import Layout from '../components/Layout';
import countryList from '../lib/countryList';
import LanguageSelector from '../components/LanguageSelector';
import { useTranslation } from 'react-i18next';

export default function SelectNationality() {
  const [country, setCountry] = useState('');
  const [search, setSearch] = useState('');
  const apiBase = import.meta.env.VITE_API_BASE;
  const userId = localStorage.getItem('user_id') || 'demo';
  const { t } = useTranslation();

  const save = async () => {
    if (!country) return;
    await fetch(`${apiBase}/user/nationality`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, nationality: country })
    });
    alert(t('select_country.saved'));
  };

  const filtered = countryList.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Layout>
      <div className="space-y-4 max-w-md mx-auto">
        <LanguageSelector />
        <h2 className="text-xl font-bold">{t('select_country.title')}</h2>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={t('select_country.search')}
          className="input input-bordered w-full"
        />
        <select
          value={country}
          onChange={e => setCountry(e.target.value)}
          className="select select-bordered w-full"
        >
          <option value="" disabled>{t('select_country.select')}</option>
          {filtered.map(c => (
            <option key={c.code} value={c.code}>{c.name}</option>
          ))}
        </select>
        <button className="btn" onClick={save}>{t('select_country.save')}</button>
      </div>
    </Layout>
  );
}
