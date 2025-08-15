import React from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { useSession } from '../hooks/useSession';
import { useTranslation } from 'react-i18next';
import DailyCard from '../components/home/DailyCard';
import StreakCard from '../components/home/StreakCard';
import CurrentIQCard from '../components/home/CurrentIQCard';
import GlobalRankCard from '../components/home/GlobalRankCard';
import UpgradeTeaser from '../components/home/UpgradeTeaser';

const API_BASE = import.meta.env.VITE_API_BASE || '';

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

  const watchAd = () => {
    fetch(`${API_BASE}/ads/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user?.id || 'demo' }),
    });
    fetch(`${API_BASE}/ads/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user?.id || 'demo' }),
    });
  };

  const dailyCount = 0;
  const streakDays = 7;
  const currentIQ = 125;
  const globalRank = 1247;

  const resetAt = new Date();
  resetAt.setHours(24, 0, 0, 0);

  const extrasEnabled = import.meta.env.VITE_ENABLED_B_EXTRAS === 'true';

  return (
    <AppShell>
      <div
        data-b-spec="home-v2"
        className="max-w-6xl mx-auto px-4 md:px-6 py-6 md:py-10 space-y-6"
      >
        <DailyCard
          count={dailyCount}
          onAnswerNext={() => navigate('/daily-survey')}
          onWatchAd={watchAd}
          onStart={handleStart}
          resetAt={resetAt}
        />

        <div className="grid gap-4 md:grid-cols-3">
          <StreakCard days={streakDays} />
          <CurrentIQCard score={currentIQ} />
          {extrasEnabled && <GlobalRankCard rank={globalRank} />}
        </div>

        {extrasEnabled && <UpgradeTeaser />}
      </div>
    </AppShell>
  );
}
