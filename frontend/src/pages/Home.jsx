import React from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Progress from '../components/ui/Progress';
import { useSession } from '../hooks/useSession';
import { useTranslation } from 'react-i18next';

export default function Home() {
  const { t } = useTranslation();
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

  const dailyCount = 0;
  const freeTries = 1;

  return (
    <AppShell>
      <div data-b-spec="home-v1" className="space-y-8">
        <section className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent gradient-primary">
            {t('landing.title', { defaultValue: 'Test your IQ and political preferences' })}
          </h1>
          <p className="text-[var(--text-muted)]">
            {t('landing.subtitle', { defaultValue: 'Take our quick IQ test and see how you compare.' })}
          </p>
          <Button onClick={handleStart} className="after:content-['→'] after:ml-2">
            {t('landing.startButton', { defaultValue: 'Start Free Test' })}
          </Button>
        </section>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="flex flex-col items-center gap-1">
            <span className="text-sm text-[var(--text-muted)]">Streak</span>
            <span className="text-xl font-bold">0</span>
          </Card>
          <Card className="flex flex-col items-center gap-1">
            <span className="text-sm text-[var(--text-muted)]">Current IQ</span>
            <span className="text-xl font-bold">--</span>
          </Card>
          {import.meta.env.VITE_ENABLED_B_EXTRAS === 'true' && (
            <Card className="flex flex-col items-center gap-1">
              <span className="text-sm text-[var(--text-muted)]">Global Rank</span>
              <span className="text-xl font-bold">--</span>
            </Card>
          )}
        </div>
        <Card className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="font-semibold">Daily 3</span>
            <span className="text-sm text-[var(--text-muted)]">{dailyCount}/3</span>
          </div>
          <Progress value={(dailyCount / 3) * 100} />
          <div className="flex gap-2">
            <Button className="flex-1" onClick={() => navigate('/daily-survey')}>
              {t('home.answer_next', { defaultValue: 'Answer next' })}
            </Button>
            <Button variant="outline" className="flex-1">
              {t('home.watch_ad', { defaultValue: 'Watch ad +1' })}
            </Button>
          </div>
        </Card>
        <Card className="space-y-4">
          <div className="flex justify-between items-center">
            <span className="font-semibold">IQ Test</span>
            <Badge variant="outline">{t('home.free', { defaultValue: 'Free' })} {freeTries}</Badge>
          </div>
          <Button onClick={handleStart} className="after:content-['→'] after:ml-2">
            {t('home.start', { defaultValue: 'Start' })}
          </Button>
        </Card>
      </div>
    </AppShell>
  );
}
