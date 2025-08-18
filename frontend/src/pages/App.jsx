import React, { useEffect, lazy, Suspense } from 'react';
import { Routes, Route, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useShareMeta from '../hooks/useShareMeta';
import AppShell from '../components/AppShell';
import ProgressBar from '../components/ProgressBar';
import Home from './Home';
import AuthCallback from './AuthCallback';
import Pricing from './Pricing';
import Upgrade from './Upgrade';
import Leaderboard from './Leaderboard';
import Arena from './Arena';
import SelectSet from './SelectSet';
import SelectNationality from './SelectNationality';
import Survey from './Survey.jsx';
import DailySurvey from './DailySurvey';
import Dashboard from './Dashboard';
import QuestionCard from '../components/QuestionCard';
import Settings from './Settings.jsx';
import DemographicsForm from './DemographicsForm.jsx';
import History from './History.jsx';
import { getQuizStart, submitQuiz } from '../api';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import Login from './Login.jsx';
import TestPage from './TestPage.jsx';
import Contact from './Contact.jsx';
import ErrorChunkReload from '../components/common/ErrorChunkReload';
import ThemeDemo from './ThemeDemo.jsx';
import Card from '../components/ui/Card';
import Progress from '../components/ui/Progress';
import UIButton from '../components/ui/Button';
import RequireAdmin from '../routes/RequireAdmin';
import RequireAuth from '../routes/RequireAuth';
import { shareResult } from '../utils/share';
import Profile from './Profile.jsx';
import Welcome from './Welcome.jsx';
import { useSession } from '../hooks/useSession';

const HomeEntry = () => {
  const { user, loading } = useSession();
  if (!loading && !user) return <Navigate to="/welcome" replace />;
  return <Home />;
};

const AdminLayout = lazy(() =>
  import('../layouts/AdminLayout').catch(err => {
    console.error('Failed to load admin chunk', err);
    return { default: () => <ErrorChunkReload chunk="admin" /> };
  })
);
const AdminHome = lazy(() => import('./AdminHome'));
const AdminQuestions = lazy(() => import('./AdminQuestions'));
const AdminSurveys = lazy(() => import('./AdminSurveys'));
const AdminUsers = lazy(() => import('./AdminUsers'));
const AdminSets = lazy(() => import('./AdminSets'));
const AdminSettings = lazy(() => import('./AdminSettings.jsx'));
const AdminQuestionStats = lazy(() => import('./AdminQuestionStats.jsx'));
const AdminPricing = lazy(() => import('./AdminPricing.jsx'));
const AdminReferral = lazy(() => import('./AdminReferral.jsx'));
const AdminPointsSettings = lazy(() => import('./AdminPointsSettings.jsx'));
const AdminPointsGrant = lazy(() => import('./AdminPointsGrant'));

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

  const { user, loading: authLoading } = useAuth();

  React.useEffect(() => {
    if (authLoading) return;
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
        setSession(data.attempt_id || data.session_id);
        setQuestions(data.questions);
        setCurrent(0);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [setId, navigate, user, authLoading]);

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
      const result = await submitQuiz(session, list, []);
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
  const { t } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      const confetti = (await import('canvas-confetti')).default;
      confetti({ particleCount: 150, spread: 70 });
    })();
  }, []);

  useShareMeta(share);


  const shareText = t('result.share_text', {
    score: Number(score).toFixed(1),
    percentile: Number(percentile).toFixed(1)
  });

  return (
    <PageTransition>
      <AppShell>
        <section data-b-spec="result-v1" className="max-w-md mx-auto space-y-8 text-center">
          <Card className="space-y-4">
            <div>
              <div className="text-5xl font-bold">{Number.isFinite(score) ? score.toFixed(1) : 'N/A'}</div>
              <p className="text-sm text-[var(--text-muted)]">IQ score</p>
            </div>
            <div className="space-y-1">
              <p className="text-sm">Percentile: {Number.isFinite(percentile) ? percentile.toFixed(1) : 'N/A'}%</p>
              <Progress value={Number.isFinite(percentile) ? percentile : 0} />
            </div>
            {share && <img src={share} alt="IQ share card" className="mx-auto rounded" />}
            {share && (
              <UIButton
                variant="outline"
                onClick={() => shareResult({ text: shareText, url: window.location.href })}
                className="w-full"
              >
                Share
              </UIButton>
            )}
            <UIButton
              onClick={() => navigate('/')}
              className="w-full after:content-['→'] after:ml-2"
            >
              {t('result.back_to_home')}
            </UIButton>
          </Card>
        </section>
      </AppShell>
    </PageTransition>
  );
};

export default function App() {
  // Admin routes are always registered for troubleshooting purposes.
  // Proper authentication is temporarily disabled.
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<HomeEntry />} />
        <Route path="/select-set" element={<RequireAuth><SelectSet /></RequireAuth>} />
        <Route path="/demographics" element={<RequireAuth><DemographicsForm /></RequireAuth>} />
        <Route path="/quiz" element={<RequireAuth><TestPage /></RequireAuth>} />
        <Route path="/test" element={<RequireAuth><TestPage /></RequireAuth>} />
        <Route path="/survey" element={<RequireAuth><Survey /></RequireAuth>} />
        <Route path="/daily-survey" element={<RequireAuth><DailySurvey /></RequireAuth>} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/upgrade" element={<Upgrade />} />
        <Route path="/contact" element={<Contact />} />
        <Route path="/result" element={<Result />} />
        <Route path="/arena" element={<Arena />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/settings/:userId" element={<RequireAuth><Settings /></RequireAuth>} />
        <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="/history/:userId" element={<RequireAuth><History /></RequireAuth>} />
        <Route path="/select-nationality" element={<RequireAuth><SelectNationality /></RequireAuth>} />
        <Route path="/login" element={<Login />} />
        <Route path="/welcome" element={<Welcome />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        {import.meta.env.DEV && (
          <Route path="/theme" element={<ThemeDemo />} />
        )}
        <Route
          path="/admin/*"
          element={
            <RequireAdmin>
              <Suspense fallback={<div />}>
                <AdminLayout />
              </Suspense>
            </RequireAdmin>
          }
        >
          <Route index element={<AdminHome />} />
          <Route path="questions" element={<AdminQuestions />} />
          <Route path="stats" element={<AdminQuestionStats />} />
          <Route path="surveys" element={<AdminSurveys />} />
          <Route path="users" element={<AdminUsers />} />
          <Route path="sets" element={<AdminSets />} />
          <Route path="settings" element={<AdminSettings />} />
          <Route path="pricing" element={<AdminPricing />} />
          <Route path="referral" element={<AdminReferral />} />
          <Route path="points/settings" element={<AdminPointsSettings />} />
          <Route path="points/grant" element={<AdminPointsGrant />} />
        </Route>
      </Routes>
    </AnimatePresence>
  );
}
