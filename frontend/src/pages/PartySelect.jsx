import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { getParties, submitPartySelection } from '../api';
import { v4 as uuidv4 } from 'uuid';

export default function PartySelect() {
  const [parties, setParties] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const [userId] = useState(() => {
    let id = localStorage.getItem('user_id');
    if (!id) {
      id = uuidv4();
      localStorage.setItem('user_id', id);
    }
    return id;
  });

  useEffect(() => {
    async function load() {
      try {
        const list = await getParties();
        setParties(list);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const toggle = (id) => {
    if (id === 12) {
      setSelected(sel => sel.includes(12) ? [] : [12]);
      return;
    }
    setSelected(sel => {
      const next = sel.includes(id) ? sel.filter(p => p !== id) : [...sel.filter(p => p !== 12), id];
      return next;
    });
  };

  const save = async () => {
    try {
      await submitPartySelection(userId, selected);
      navigate('/');
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <Layout>
      <div className="p-4 space-y-4 max-w-md mx-auto">
        <h2 className="text-xl font-bold text-center">Select Party</h2>
        {loading && <p>Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}
        {!loading && (
          <div className="space-y-2">
            {parties.map(p => (
              <label key={p.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={selected.includes(p.id)}
                  onChange={() => toggle(p.id)}
                  className="h-4 w-4"
                />
                <span>{p.name}</span>
              </label>
            ))}
          </div>
        )}
        <button
          onClick={save}
          className="w-full px-4 py-2 rounded-md bg-primary text-white"
        >
          Save
        </button>
      </div>
    </Layout>
  );
}
