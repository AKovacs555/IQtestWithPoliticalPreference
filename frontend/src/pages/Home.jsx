import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { useSession } from '../hooks/useSession';
import { useTranslation } from 'react-i18next';
import CurrentIQCard from '../components/home/CurrentIQCard';
import GlobalRankCard from '../components/home/GlobalRankCard';
import Daily3Banner from '../components/home/Daily3Banner';
import TestStartBanner from '../components/home/TestStartBanner';
import UpgradeTeaser from '../components/home/UpgradeTeaser';
import HeroTop from '../components/layout/HeroTop';
import ArenaBanner from '../components/home/ArenaBanner';

export default function Home() {
  const { t, i18n } = useTranslation();
  const { user, loading, session, userId } = useSession();
  const navigate = useNavigate();
  const apiBase = import.meta.env.VITE_API_BASE || '';

  const authHeaders = session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {};

  const [points, setPoints] = useState(0);
  const [inviteCode, setInviteCode] = useState('');
  const [currentIQ, setCurrentIQ] = useState(0);
  const [globalRank, setGlobalRank] = useState(null);

  const fetchCredits = async () => {
    if (!session?.access_token) return;
    try {
      const headers = { Authorization: `Bearer ${session.access_token}` };
      const [credRes, codeRes, histRes] = await Promise.all([
        fetch(`${apiBase}/user/credits`, { headers, credentials: 'include' }),
        fetch(`${apiBase}/referral/code`, { headers, credentials: 'include' }),
        userId
          ? fetch(`${apiBase}/stats/iq_histogram?user_id=${userId}`)
          : Promise.resolve(null),
      ]);
      if (credRes?.ok) {
        const d = await credRes.json();
        setPoints(d.points ?? 0);
      }
      if (codeRes?.ok) {
        const d = await codeRes.json();
        setInviteCode(d.invite_code || '');
      }
      if (histRes && histRes.ok) {
        const h = await histRes.json();
        setCurrentIQ(h.user_score || 0);
      }
    } catch {}
  };

  useEffect(() => {
    fetchCredits();
  }, [session, userId]);

  useEffect(() => {
    if (!userId) return;
    fetch(`${apiBase}/leaderboard?limit=1000`)
      .then((r) => r.json())
      .then((d) => {
        const idx = d.leaderboard?.findIndex((x) => x.user_id === userId);
        if (idx != null && idx >= 0) setGlobalRank(idx + 1);
      })
      .catch(() => {});
  }, [userId, apiBase]);

  const handleAnswerNext = async () => {
    if (loading) return;
    if (!user) {
      navigate('/login');
      return;
    }
    try {
      const res = await fetch(
        `${apiBase}/survey/start?lang=${i18n.language}`,
        { headers: authHeaders, credentials: 'include' },
      );
      if (res.ok) {
        const payload = await res.json();
        navigate(`/survey?sid=${payload.survey.id}`, { state: payload });
      } else if (res.status === 404 || res.status === 204) {
        await handleStartQuiz();
      }
    } catch {}
  };

  const handleStartQuiz = async () => {
    if (loading) return;
    if (!user) {
      navigate('/login');
      return;
    }
    try {
      const res = await fetch(
        `${apiBase}/quiz/start?lang=${i18n.language}`,
        { headers: authHeaders, credentials: 'include' },
      );
      if (res.ok) {
        const payload = await res.json();
        await fetchCredits();
        navigate(`/quiz?attempt_id=${payload.attempt_id}`, { state: payload });
      } else {
        const err = await res.json().catch(() => ({}));
        if (err?.detail?.code === 'DAILY3_REQUIRED') {
          await handleAnswerNext();
          return;
        }
        if (
          err?.detail?.error === 'insufficient_points' ||
          err?.error === 'insufficient_points'
        ) {
          alert('ポイントが不足しています。');
          return;
        }
        if (
          err?.detail?.error === 'survey_required' ||
          err?.error === 'survey_required'
        ) {
          const s = await fetch(
            `${apiBase}/survey/start?lang=${i18n.language}`,
            { headers: authHeaders, credentials: 'include' },
          );
          if (s.ok) {
            const p = await s.json();
            navigate(`/survey?sid=${p.survey.id}`);
            return;
          }
        }
      }
    } catch {}
  };

  const dailyProgressPct = 0;
  const dailyResetText = '';
  const handleWatchAd = async () => {
    await fetchCredits();
  };

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto px-4 md:px-8 py-6 md:py-10 space-y-6">
        {/* 上部ロゴ＋小ピル群（B と同仕様） */} {/* data-b-spec: hero-top */}
        <HeroTop />

        <Daily3Banner
          progress={dailyProgressPct}
          onNext={handleAnswerNext}
          onWatchAd={handleWatchAd}
          resetText={dailyResetText}
        />
        <TestStartBanner
          onStart={handleStartQuiz}
          statRight={{ value: String(points), label: 'ポイント' }}
        />
        <ArenaBanner />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <CurrentIQCard score={currentIQ} inviteCode={inviteCode} />
          <GlobalRankCard rank={globalRank ?? '-'} />
        </div>
        <UpgradeTeaser />
      </div>
    </AppShell>
  );
}
