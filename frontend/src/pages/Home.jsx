import React from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { useSession } from '../hooks/useSession';
import { useTranslation } from 'react-i18next';
import StreakCard from '../components/home/StreakCard';
import CurrentIQCard from '../components/home/CurrentIQCard';
import GlobalRankCard from '../components/home/GlobalRankCard';
import Daily3Banner from '../components/home/Daily3Banner';
import TestStartBanner from '../components/home/TestStartBanner';
import UpgradeTeaser from '../components/home/UpgradeTeaser';
import HeroTop from '../components/layout/HeroTop';

export default function Home() {
  const { i18n } = useTranslation();
  const { user, loading, session } = useSession();
  const navigate = useNavigate();
  const apiBase = import.meta.env.VITE_API_BASE || '';

  const authHeaders = session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {};

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
        navigate(`/survey?sid=${payload.survey.id}`);
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
        navigate(`/quiz/play?attempt_id=${payload.attempt_id}`);
      } else {
        const err = await res.json().catch(() => ({}));
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

  const streakDays = 7;
  const currentIQ = 125;
  const globalRank = 1247;
  const dailyProgressPct = 0;
  const dailyResetText = '';
  const handleWatchAd = () => {};

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
        <TestStartBanner onStart={handleStartQuiz} />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StreakCard days={streakDays} />
          <CurrentIQCard score={currentIQ} />
          <GlobalRankCard rank={globalRank} />
        </div>
        <UpgradeTeaser />
      </div>
    </AppShell>
  );
}
