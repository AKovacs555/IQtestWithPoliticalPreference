import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Button from '../components/ui/Button';
import { useSession } from '../hooks/useSession';
import { useTranslation } from 'react-i18next';
import DailyCard from '../components/home/DailyCard';
import StreakCard from '../components/home/StreakCard';
import CurrentIQCard from '../components/home/CurrentIQCard';
import GlobalRankCard from '../components/home/GlobalRankCard';
import UpgradeTeaser from '../components/home/UpgradeTeaser';

const API_BASE = import.meta.env.VITE_API_BASE || '';

export default function Home() {
  const { t } = useTranslation();
  const { user, loading } = useSession();
  const navigate = useNavigate();
  const [adProgress, setAdProgress] = useState(0);

  const handleStart = () => {
    if (loading) return;
    if (!user) navigate('/login');
    else if (!localStorage.getItem('nationality')) navigate('/select-nationality');
    else if (localStorage.getItem('demographic_completed') !== 'true') navigate('/demographics');
    else if (localStorage.getItem('survey_completed') !== 'true') navigate('/survey');
    else navigate('/quiz');
  };

  const watchAd = () => {
    setAdProgress(0);
    fetch(`${API_BASE}/ads/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: user?.id || 'demo' }),
    });
    const id = setInterval(() => {
      setAdProgress((p) => {
        if (p >= 100) {
          clearInterval(id);
          fetch(`${API_BASE}/ads/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user?.id || 'demo' }),
          });
          return 100;
        }
        return p + 10;
      });
    }, 300);
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
      <div data-b-spec="home-v1" className="max-w-4xl mx-auto space-y-12">
        <section className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent gradient-primary">
            あなたのポテンシャルを解き放とう！
          </h1>
          <p className="text-[var(--text-muted)]">毎日3問に答えてIQテストを受けましょう</p>
          <Button onClick={handleStart} className="shine glow ring-brand mx-auto">
            無料IQテストを始める
          </Button>
        </section>

        <DailyCard
          count={dailyCount}
          onAnswerNext={() => navigate('/daily-survey')}
          onWatchAd={watchAd}
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
