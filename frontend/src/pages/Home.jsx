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
import StatisticsBanner from '../components/StatisticsBanner';
import { supabase } from '../lib/supabaseClient';

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
      // Fetch points and referral code
      const [credRes, codeRes] = await Promise.all([
        fetch(`${apiBase}/user/credits`, { headers, credentials: 'include' }),
        fetch(`${apiBase}/referral/code`, { headers, credentials: 'include' })
      ]);
      if (credRes.ok) {
        const d = await credRes.json();
        setPoints(d.points ?? 0);
      }
      if (codeRes.ok) {
        const d = await codeRes.json();
        setInviteCode(d.invite_code || '');
      }
      if (userId) {
        const { data: userData } = await supabase
          .from('app_users')
          .select('hashed_id')
          .eq('id', userId)
          .single();
        const hashedId = userData?.hashed_id;
        if (hashedId) {
          const histRes = await fetch(
            `${apiBase}/stats/iq_histogram?user_id=${hashedId}`
          );
          if (histRes.ok) {
            const h = await histRes.json();
            setCurrentIQ(h.user_score || 0);
          }
        }
      }
      const lbRes = await fetch(`${apiBase}/leaderboard?limit=1`, {
        headers: authHeaders,
        credentials: 'include',
      });
      if (lbRes.ok) {
        const d = await lbRes.json();
        setGlobalRank(d.my_rank ?? null);
      }
    } catch {
      /* handle errors if needed */
    }
  };

  useEffect(() => {
    fetchCredits();
  }, [session, userId]);

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
        const code = err?.detail?.code || err?.detail?.error || err?.error;
        if (code === 'DAILY3_REQUIRED') {
          await handleAnswerNext();
          return;
        }
        if (code === 'insufficient_points') {
          alert('ポイントが不足しています。');
          return;
        }
        if (code === 'survey_required') {
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
        if (code === 'nationality_required') {
          navigate('/country');
          return;
        }
        if (code === 'demographic_required') {
          navigate('/demographics');
          return;
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

        <StatisticsBanner />
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
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <CurrentIQCard score={currentIQ} inviteCode={inviteCode} />
          <GlobalRankCard rank={globalRank ?? '-'} />
        </div>
        <UpgradeTeaser />
      </div>
    </AppShell>
  );
}
