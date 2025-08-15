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
  useTranslation();
  const { user, loading } = useSession();
  const navigate = useNavigate();

  const handleStart = () => {
    if (loading) return;
    if (!user) navigate('/login');
    else if (!localStorage.getItem('nationality')) navigate('/select-nationality');
    else if (localStorage.getItem('demographic_completed') !== 'true') navigate('/demographics');
    else if (localStorage.getItem('survey_completed') !== 'true') navigate('/survey');
    else navigate('/quiz');
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
          onNext={handleStart}
          onWatchAd={handleWatchAd}
          resetText={dailyResetText}
        />
        <TestStartBanner onStart={handleStart} />
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
