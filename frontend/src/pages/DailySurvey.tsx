import React, { useEffect, useState } from 'react';
import SurveyCard from '../components/survey/SurveyCard';

export default function DailySurvey() {
  const [items, setItems] = useState<any[]>([]);
  const [current, setCurrent] = useState(0);
  const [done, setDone] = useState(false);
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    fetch(`${apiBase}/surveys/daily3?lang=ja`, { headers })
      .then(r => r.json())
      .then(d => setItems(d.items || []))
      .catch(() => setItems([]));
  }, []);

  const handleAnswer = async (idx: number) => {
    const item = items[current];
    await fetch(`${apiBase}/surveys/answer`, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ item_id: item.id, answer_index: idx }),
    });
    if (current + 1 < items.length) setCurrent(current + 1);
    else setDone(true);
  };

  if (done || items.length === 0) {
    return (
      <div className="max-w-screen-md lg:max-w-screen-lg px-4 md:px-6 space-y-4 mx-auto text-center">
        <p>当日分は完了しました</p>
      </div>
    );
  }

  return (
    <div className="max-w-screen-md lg:max-w-screen-lg px-4 md:px-6 space-y-4 mx-auto">
      <SurveyCard item={items[current]} onAnswer={handleAnswer} />
    </div>
  );
}
