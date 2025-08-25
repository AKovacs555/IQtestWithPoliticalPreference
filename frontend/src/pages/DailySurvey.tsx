import React, { useEffect, useState } from 'react';
import SurveyCard from '../components/survey/SurveyCard';
import { useSession } from '../hooks/useSession';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { supabase } from '../lib/supabaseClient';
import { fetchSurveyFeed } from '../lib/supabase/feed';
import { USE_RPC_FEED } from '../lib/env';

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


async function fetchSurveysLegacy(apiBase: string, lang: string, headers: Record<string, string>) {
  const res = await fetch(`${apiBase}/surveys/daily3?lang=${lang}`, { headers });
  if (!res.ok) {
    if (res.status === 409) {
      const err = await res.json().catch(() => ({}));
      if (err?.detail?.error === 'daily_quota_exceeded') {
        return { items: [], done: true };
      }
    }
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || 'Failed to load.');
  }
  const d = await res.json();
  return { items: d.items || [], done: false };
}

export default function DailySurvey() {
  const [items, setItems] = useState<any[]>([]);
  const [current, setCurrent] = useState(0);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingIdx, setPendingIdx] = useState<number | null>(null);
  const [answeredToday, setAnsweredToday] = useState<boolean | null>(null);
  const apiBase = import.meta.env.VITE_API_BASE || '';
  const { session } = useSession();
  const { i18n } = useTranslation();
  const headers = session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
  const navigate = useNavigate();
  useEffect(() => {
    async function checkAnswered() {
      const ok = await supabase.rpc('me_has_answered_today');
      if (ok.error) throw ok.error;
      setAnsweredToday(ok.data === true);
    }
    checkAnswered().catch((e) => setError(e.message));
  }, []);

  const load = async () => {
    try {
      setError(null);
      const lang = i18n?.language ?? null;

      if (USE_RPC_FEED) {
        const rows = await fetchSurveyFeed(supabase, lang, 3, 0);
        if (!rows.length) {
          setDone(true);
          return;
        }
        const items = rows.map((r) => ({
          ...r,
          question: (r as any).question ?? r.question_text,
          body: (r as any).body ?? r.question_text,
          choices: (r as any).choices ?? r.options,
        }));
        setItems(items);
      } else {
        const legacy = await fetchSurveysLegacy(apiBase, lang || 'en', headers);
        if (legacy.done || legacy.items.length === 0) {
          toast.info('Daily 3 completed!');
          setDone(true);
          return;
        }
        const items = legacy.items.map((r) => ({
          ...r,
          question: (r as any).question ?? r.question_text,
          body: (r as any).body ?? r.question_text,
          choices: (r as any).choices ?? r.options,
        }));
        setItems(items);
      }
    } catch (e: any) {
      setError(e.message || 'ネットワークエラーが発生しました。');
    }
  };

  useEffect(() => {
    const nat = localStorage.getItem('nationality');
    if (!nat) {
      navigate('/select-nationality');
      return;
    }
    if (answeredToday === true) {
      toast.info('Daily 3 completed!');
      setDone(true);
      return;
    }
    if (session && answeredToday === false) load();
  }, [session, navigate, answeredToday]);

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
