import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';

export default function SelectParty() {
  const [parties, setParties] = useState([]);
  const [selected, setSelected] = useState([]);
  const apiBase = import.meta.env.VITE_API_BASE;
  const userId = localStorage.getItem('user_id') || 'demo';
  const nationality = localStorage.getItem('nationality') || 'US';
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetch(`${apiBase}/user/parties/${nationality}`)
      .then(r => r.json())
      .then(d => setParties(d.parties || []));
  }, []);

  const toggle = (id) => {
    setSelected(s => {
      if (id === 12) {
        return s.includes(12) ? [] : [12];
      }
      const withoutNo = s.filter(i => i !== 12);
      return withoutNo.includes(id) ? withoutNo.filter(i => i !== id) : [...withoutNo, id];
    });
  };

  const save = async () => {
    if (selected.length === 0) {
      alert(t('select_party.select_error'));
      return;
    }
    await fetch(`${apiBase}/user/party`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, party_ids: selected })
    });
    localStorage.setItem('party_selected', '1');
    alert(t('select_party.saved'));
    navigate('/select-set');
  };

  return (
    <Layout>
      <div className="space-y-2 max-w-md mx-auto">
        <h2 className="text-xl font-bold mb-2">{t('select_party.title')}</h2>
        {parties.map(p => {
          const noAff = selected.includes(12);
          const disabled = (noAff && p.id !== 12) || (!noAff && selected.length > 0 && p.id === 12);
          return (
            <label key={p.id} className={`flex items-center space-x-2 ${disabled ? 'opacity-50' : ''}`}>
              <input
                type="checkbox"
                checked={selected.includes(p.id)}
                disabled={disabled}
                onChange={() => toggle(p.id)}
              />
              <span>{p.name}</span>
            </label>
          );
        })}
        <button className="btn" onClick={save}>{t('select_party.save')}</button>
      </div>
    </Layout>
  );
}
