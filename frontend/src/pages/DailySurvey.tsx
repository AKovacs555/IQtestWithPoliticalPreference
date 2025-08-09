import React, { useEffect, useState } from 'react';
import SurveyCard from '../components/survey/SurveyCard';

// minimal toast shim
const toast = {
  info: (msg: string) => {
    if (typeof window !== 'undefined' && (window as any).toast) {
      (window as any).toast(msg);
    } else {
      // eslint-disable-next-line no-alert
      alert(msg);
    }
  },
};

export default function DailySurvey() {
  const [items, setItems] = useState<any[]>([]);
  const [current, setCurrent] = useState(0);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingIdx, setPendingIdx] = useState<number | null>(null);
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const load = async () => {
    try {
      setError(null);
      const res = await fetch(`${apiBase}/surveys/daily3?lang=ja`, { headers });
      if (!res.ok) {
        if (res.status === 409) {
          toast.info('Daily 3 completed!');
          setDone(true);
          return;
        }
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || 'Failed to load.');
      }
      const d = await res.json();
      setItems(d.items || []);
    } catch (e: any) {
      setError(e.message || 'ネットワークエラーが発生しました。');
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleAnswer = async (idx: number) => {
    const item = items[current];
    try {
      const res = await fetch(`${apiBase}/surveys/answer`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: item.id, answer_index: idx }),
      });
      if (!res.ok) {
        if (res.status === 409) {
          const err = await res.json().catch(() => ({}));
          if (err?.detail?.error === 'daily_quota_exceeded') {
            toast.info('Daily 3 completed!');
            setDone(true);
            return;
          }
          if (err?.detail?.error === 'already_answered') {
            throw new Error('Already answered');
          }
        }
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || 'Failed to submit.');
      }
      if (current + 1 < items.length) setCurrent(current + 1);
      else setDone(true);
    } catch (e: any) {
      setError(e.message);
      setPendingIdx(idx);
    }
  };

  if (error) {
    return (
      <div className="max-w-screen-md lg:max-w-screen-lg px-4 md:px-6 space-y-4 mx-auto text-center">
        <p>{error}</p>
        <button
          className="px-4 py-2 rounded bg-[var(--btn-primary)] text-white"
          onClick={() => {
            if (pendingIdx !== null) {
              const idx = pendingIdx;
              setPendingIdx(null);
              handleAnswer(idx);
            } else {
              load();
            }
          }}
        >
          再試行
        </button>
      </div>
    );
  }

  if (done || items.length === 0) {
    return (
      <div className="max-w-screen-md lg:max-w-screen-lg px-4 md:px-6 space-y-4 mx-auto text-center">
        <p>Daily 3 completed</p>
        <a
          className="px-4 py-2 rounded bg-[var(--btn-primary)] text-white"
          href="/quiz"
        >
          Start IQ test
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-screen-md lg:max-w-screen-lg px-4 md:px-6 space-y-4 mx-auto">
      <SurveyCard item={items[current]} onAnswer={handleAnswer} />
    </div>
  );
}
