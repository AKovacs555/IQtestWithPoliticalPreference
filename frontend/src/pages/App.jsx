import React, { useEffect, useState, lazy, Suspense } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useShareMeta from '../hooks/useShareMeta';
import { useAuth } from '../auth/useAuth';
import AppShell from '../components/AppShell';
import ProgressBar from '../components/ProgressBar';
import Home from './Home';
import AuthCallback from './AuthCallback';
import Pricing from './Pricing';
import Leaderboard from './Leaderboard';
import SelectSet from './SelectSet';
import SelectNationality from './SelectNationality';
import SurveyPage from './SurveyPage';
import DailySurvey from './DailySurvey';
import Dashboard from './Dashboard';
import QuestionCard from '../components/QuestionCard';
import Settings from './Settings.jsx';
import DemographicsForm from './DemographicsForm.jsx';
import History from './History.jsx';
import { getQuizStart, submitQuiz } from '../api';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import SignupPage from './SignupPage.jsx';
import LoginPage from './LoginPage.jsx';
import TestPage from './TestPage.jsx';
import Contact from './Contact.jsx';
import ErrorChunkReload from '../components/common/ErrorChunkReload';
import ThemeDemo from './ThemeDemo.jsx';
import Button from '@mui/material/Button';
import RequireAdmin from '../components/RequireAdmin';
import { shareResult, buildLineShareUrl, buildFacebookShareUrl } from '../utils/share';
const API_BASE = import.meta.env.VITE_API_BASE || "";

const AdminLayout = lazy(() =>
  import('../layouts/AdminLayout').catch(err => {
    console.error('Failed to load admin chunk', err);
    return { default: () => <ErrorChunkReload chunk="admin" /> };
  })
);
const AdminHome = lazy(() => import('./AdminHome'));
const AdminQuestions = lazy(() => import('./AdminQuestions'));
const AdminSurvey = lazy(() => import('./AdminSurvey'));
const AdminUsers = lazy(() => import('./AdminUsers'));
const AdminSets = lazy(() => import('./AdminSets'));
const AdminSettings = lazy(() => import('./AdminSettings.jsx'));
const AdminQuestionStats = lazy(() => import('./AdminQuestionStats.jsx'));
const AdminPricing = lazy(() => import('./AdminPricing.jsx'));
const AdminReferral = lazy(() => import('./AdminReferral.jsx'));

const PageTransition = ({ children }) => {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={reduce ? { opacity: 0 } : { opacity: 0, y: 20 }}
      animate={reduce ? { opacity: 1 } : { opacity: 1, y: 0 }}
      exit={reduce ? { opacity: 0 } : { opacity: 0, y: -20 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      {children}
    </motion.div>
  );
};


const Quiz = () => {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const setId = params.get('set');
  const [session, setSession] = React.useState(null);
  const [questions, setQuestions] = React.useState([]);
  const [answers, setAnswers] = React.useState([]);
  const [current, setCurrent] = React.useState(0);
  const [timeLeft, setTimeLeft] = React.useState(300);
  const [suspicious, setSuspicious] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [submitting, setSubmitting] = React.useState(false);
  const { t } = useTranslation();
  const navigate = useNavigate();
  const watermark = React.useMemo(() => `${session?.slice(0,6) || ''}-${Date.now()}`,[session]);

  const { user } = useAuth();

  React.useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    const nat = localStorage.getItem('nationality');
    if (!nat) {
      navigate('/select-nationality');
      return;
    }
    if (localStorage.getItem('demographic_completed') !== 'true') {
      navigate('/demographics');
      return;
    }
    if (localStorage.getItem('survey_completed') !== 'true') {
      navigate('/survey');
      return;
    }
    async function load() {
      try {
        const data = await getQuizStart(setId, undefined);
        setSession(data.session_id);
        setQuestions(data.questions);
        setCurrent(0);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [setId, navigate, user]);

  // Prevent copying or cutting text and disable context menu
  React.useEffect(() => {
    const preventCopy = (e) => e.preventDefault();
    const preventContext = (e) => e.preventDefault();
    document.addEventListener('copy', preventCopy);
    document.addEventListener('cut', preventCopy);
    document.addEventListener('contextmenu', preventContext);
    return () => {
      document.removeEventListener('copy', preventCopy);
      document.removeEventListener('cut', preventCopy);
      document.removeEventListener('contextmenu', preventContext);
    };
  }, []);

  React.useEffect(() => {
    const t = setInterval(() => setTimeLeft(t => Math.max(t - 1, 0)), 1000);
    return () => clearInterval(t);
  }, []);

  const submit = async (list) => {
    if (submitting) return;
    setSubmitting(true);
    try {
      // console.log('submitQuiz called');
      const result = await submitQuiz(session, list);
      const params = new URLSearchParams({
        iq: result.iq.toString(),
        percentile: result.percentile.toString(),
      });
      if (result.share_url) params.set('share_url', result.share_url);
      navigate('/result?' + params.toString());
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  React.useEffect(() => {
    if (timeLeft === 0 && !loading && !error) {
      (async () => {
        await submit(
          answers.map((ans, idx) => ({
            id: questions[idx].id,
            answer: ans ?? -1,
          }))
        );
      })();
    }
  }, [timeLeft, loading, error]);

  React.useEffect(() => {
    let hideTime = null;
    const onHide = () => { hideTime = Date.now(); };
    const onShow = () => {
      if (hideTime && Date.now() - hideTime > 3000) setSuspicious(true);
      hideTime = null;
    };
    // Flag the attempt if the user switches tabs or apps for too long.
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) onHide(); else onShow();
    });
    window.addEventListener('blur', onHide);
    window.addEventListener('focus', onShow);
    return () => {
      document.removeEventListener('visibilitychange', () => {});
      window.removeEventListener('blur', onHide);
      window.removeEventListener('focus', onShow);
    };
  }, []);

  const select = async (i) => {
    if (submitting) return;
    const a = [...answers];
    a[current] = i;
    setAnswers(a);
    if (current + 1 < questions.length) {
      setCurrent(c => c + 1);
    } else {
      await submit(a.map((ans, idx) => ({ id: questions[idx].id, answer: ans })));
    }
  };

  return (
    <PageTransition>
      <AppShell>
        <div className="space-y-4 max-w-lg mx-auto quiz-container">
          {loading && <p>Loading...</p>}
          {error && <p className="text-red-600">{error}</p>}
          {!loading && !error && (
            <>
              <div className="flex justify-between items-center">
                <span className="text-sm font-mono">
                  {t('quiz.progress', { current: current + 1, total: questions.length })}
                </span>
                <div className="text-right font-mono">
                  {Math.floor(timeLeft / 60)}:{`${timeLeft % 60}`.padStart(2, '0')}
                </div>
              </div>
              <ProgressBar value={(current / questions.length) * 100} />
              {questions[current] && (
                <QuestionCard
                  question={questions[current]}
                  onSelect={select}
                  watermark={watermark}
                  disabled={submitting}
                />
              )}
            </>
          )}
          {suspicious && (
            <p className="text-red-600 text-sm">Session flagged for leaving the page.</p>
          )}
        </div>
      </AppShell>
    </PageTransition>
  );
};

// Survey component moved to SurveyPage.jsx

const Result = () => {
  const location = useLocation();
  console.log('location.search:', location.search);
  const params = new URLSearchParams(location.search);
  console.log('params:', Array.from(params.entries()));
  const iqParam = params.get('iq');
  const percentileParam = params.get('percentile');
  const shareParam = params.get('share_url');
  const share =
    shareParam && shareParam !== 'null' && shareParam !== 'undefined' ? shareParam : null;
  const score = iqParam ? Number(iqParam) : NaN;
  const percentile = percentileParam ? Number(percentileParam) : NaN;
  const [avg, setAvg] = React.useState(null);
  const { t } = useTranslation();
  const price = import.meta.env.VITE_PRO_PRICE_MONTHLY;
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      const confetti = (await import('canvas-confetti')).default;
      confetti({ particleCount: 150, spread: 70 });
    })();
  }, []);

  useShareMeta(share);

  useEffect(() => {
    fetch(`${API_BASE}/leaderboard`)
      .then(res => res.json())
      .then(data => {
        const all = data.leaderboard.map(l => l.avg_iq);
        if (all.length) setAvg(all.reduce((a,b) => a+b,0)/all.length);
      });
  }, []);

  const shareText = t('result.share_text', {
    score: Number(score).toFixed(1),
    percentile: Number(percentile).toFixed(1)
  });

  return (
    <PageTransition>
      <AppShell>
        <div className="text-center space-y-4 p-6 max-w-md mx-auto rounded-2xl backdrop-blur-md bg-white/60 shadow-lg">
          <h2 className="text-2xl font-bold">Your Results</h2>
          <p>IQ: {Number.isFinite(score) ? score.toFixed(2) : 'N/A'}</p>
          <p>Percentile: {Number.isFinite(percentile) ? percentile.toFixed(1) : 'N/A'}%</p>
          <span className="text-xs text-gray-500" title="Scores are for entertainment and may not reflect a clinical IQ">what's this?</span>
          {avg && <p className="text-sm">Overall average IQ: {avg.toFixed(1)}</p>}
          {share && <img src={share} alt="IQ share card" className="mx-auto rounded" />}
          {share && (
            <div className="space-x-2">
              <Button
                onClick={() => shareResult({ text: shareText, url: window.location.href })}
                variant="contained"
                size="small"
              >
                X
              </Button>
              <Button
                component="a"
                href={buildLineShareUrl(window.location.href)}
                target="_blank"
                rel="noreferrer"
                variant="contained"
                size="small"
              >
                LINE
              </Button>
              <Button
                component="a"
                href={buildFacebookShareUrl(window.location.href)}
                target="_blank"
                rel="noreferrer"
                variant="contained"
                size="small"
              >
                Facebook
              </Button>
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href);
                  alert(t('result.link_copied'));
                }}
                variant="contained"
                size="small"
              >
                Copy
              </Button>
            </div>
          )}
          <Button
            onClick={() => navigate('/')}
            variant="contained"
            size="small"
            sx={{ mt: 4 }}
          >
            {t('result.back_to_home')}
          </Button>
          <div className="mt-4 space-y-2">
            <p>{t('result.pro_prompt', { price })}</p>
            <Button
              component="a"
              href="/pricing"
              variant="contained"
              size="small"
            >
              {t('pricing.subscribe')}
            </Button>
          </div>
          <p className="text-sm text-gray-600">This test is for research and entertainment.</p>
        </div>
      </AppShell>
    </PageTransition>
  );
};

export default function App() {
  // Admin routes are always registered for troubleshooting purposes.
  // Proper authentication is temporarily disabled.
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const u = new URL(window.location.href);
    if (u.pathname === '/' && u.searchParams.get('code')) {
      navigate('/auth/callback' + u.search, { replace: true });
    }
  }, [navigate]);
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home />} />
        <Route path="/select-set" element={<SelectSet />} />
        <Route path="/demographics" element={<DemographicsForm />} />
        <Route path="/quiz" element={<TestPage />} />
        <Route path="/test" element={<TestPage />} />
        <Route path="/survey" element={<SurveyPage />} />
        <Route path="/daily-survey" element={<DailySurvey />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/result" element={<Result />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings/:userId" element={<Settings />} />
        <Route path="/history/:userId" element={<History />} />
        <Route path="/select-nationality" element={<SelectNationality />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        {import.meta.env.DEV && (
          <Route path="/theme" element={<ThemeDemo />} />
        )}
        <Route
          path="/admin/*"
          element={
            <Suspense fallback={<div />}>
              <RequireAdmin>
                <AdminLayout />
              </RequireAdmin>
            </Suspense>
          }
        >
          <Route index element={<AdminHome />} />
          <Route path="questions" element={<AdminQuestions />} />
          <Route path="stats" element={<AdminQuestionStats />} />
          <Route path="surveys" element={<AdminSurvey />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="sets" element={<AdminSets />} />
          <Route path="settings" element={<AdminSettings />} />
          <Route path="pricing" element={<AdminPricing />} />
          <Route path="referral" element={<AdminReferral />} />
        </Route>
      </Routes>
    </AnimatePresence>
  );
}
