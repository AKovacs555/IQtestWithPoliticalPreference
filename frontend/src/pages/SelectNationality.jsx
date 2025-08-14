import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import getCountryList from '../lib/countryList';
import LanguageSelector from '../components/LanguageSelector';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../hooks/useSession';

export default function SelectNationality() {
  const [country, setCountry] = useState('');
  const [search, setSearch] = useState('');
  const [list, setList] = useState([]);
  const apiBase = import.meta.env.VITE_API_BASE;
  const { userId } = useSession();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    setList(getCountryList(i18n.language));
  }, [i18n.language]);

  const save = async () => {
    if (!country) {
      alert(t('select_country.select'));
      return;
    }
    await fetch(`${apiBase}/user/nationality`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, nationality: country })
    });
    localStorage.setItem('nationality', country);
    localStorage.setItem('survey_completed', 'false');
    localStorage.setItem('demographic_completed', 'false');
    alert(t('select_country.saved'));
    navigate('/demographics');
  };

  const filtered = list.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppShell>
      <div className="space-y-4 max-w-md mx-auto">
        <LanguageSelector />
        <h2 className="text-xl font-bold">{t('select_country.title')}</h2>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={t('select_country.search')}
          className="w-full border rounded-md px-3 py-2"
        />
        <select
          value={country}
          onChange={e => setCountry(e.target.value)}
          className="w-full border rounded-md px-3 py-2"
        >
          <option value="" disabled>{t('select_country.select')}</option>
          {filtered.map(c => (
            <option key={c.code} value={c.code}>{c.name}</option>
          ))}
        </select>
        <button
          className="px-4 py-2 rounded-md bg-primary text-white"
          onClick={save}
        >
          {t('select_country.save')}
        </button>
      </div>
    </AppShell>
  );
}
