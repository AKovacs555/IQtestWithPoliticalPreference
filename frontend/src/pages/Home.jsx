import React from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { useSession } from '../hooks/useSession';
import { useTranslation } from 'react-i18next';
import CurrentIQCard from '../components/home/CurrentIQCard';
import GlobalRankCard from '../components/home/GlobalRankCard';
import StreakCard from '../components/home/StreakCard';
import TakeTestCard from '../components/home/TakeTestCard';
import UpgradeTeaser from '../components/home/UpgradeTeaser';

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

  return (
    <AppShell>
      <div
        data-b-spec="home-v2"
        className="max-w-6xl mx-auto px-4 md:px-8 py-8 md:py-12 space-y-6"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <CurrentIQCard score={currentIQ} />
          <GlobalRankCard rank={globalRank} />
          <StreakCard days={streakDays} />
          <TakeTestCard onStart={handleStart} />
        </div>
        <UpgradeTeaser />
      </div>
    </AppShell>
  );
}
