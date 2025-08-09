import React, { useEffect, useState } from 'react';

export default function AdminSurvey() {
  const [surveys, setSurveys] = useState<any[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [items, setItems] = useState<any[]>([]);
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const loadSurveys = async () => {
    const res = await fetch(`${apiBase}/admin/surveys`, { headers });
    const data = await res.json();
    setSurveys(data.surveys || []);
  };

  const loadItems = async (id: string) => {
    const res = await fetch(`${apiBase}/admin/surveys/${id}/items`, { headers });
    const data = await res.json();
    setItems(data.items || []);
  };

  useEffect(() => {
    loadSurveys();
  }, []);

  const createSurvey = async () => {
    const title = prompt('Title');
    if (!title) return;
    await fetch(`${apiBase}/admin/surveys`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    loadSurveys();
  };

  const addItem = async () => {
    if (!selected) return;
    const body = prompt('Question body');
    if (!body) return;
    const choices = prompt('Choices comma separated')?.split(',') || [];
    await fetch(`${apiBase}/admin/surveys/${selected}/items`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ body, choices, order_no: items.length }),
    });
    loadItems(selected);
  };

  const deleteItem = async (id: string) => {
    await fetch(`${apiBase}/admin/surveys/items/${id}`, { method: 'DELETE', headers });
    if (selected) loadItems(selected);
  };

  return (
    <div className="max-w-screen-lg mx-auto px-4 md:px-6 space-y-4">
      <h1 className="text-xl font-bold">Surveys</h1>
      <button className="rounded bg-[var(--btn-primary)] text-white px-4 py-2" onClick={createSurvey}>New Survey</button>
      <ul className="space-y-2">
        {surveys.map(s => (
          <li key={s.id} className="cursor-pointer" onClick={() => { setSelected(s.id); loadItems(s.id); }}>
            {s.title}
          </li>
        ))}
      </ul>
      {selected && (
        <div className="space-y-2 mt-4">
          <h2 className="font-semibold">Items</h2>
          <button className="rounded bg-[var(--btn-neutral)] text-white px-4 py-2" onClick={addItem}>Add Item</button>
          <ul className="space-y-1">
            {items.map(it => (
              <li key={it.id} className="flex justify-between">
                <span>{it.body}</span>
                <button className="rounded bg-[var(--btn-destructive)] text-white px-2" onClick={() => deleteItem(it.id)}>Delete</button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
