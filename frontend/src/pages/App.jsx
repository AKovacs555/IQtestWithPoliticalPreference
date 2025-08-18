import React, { useEffect, lazy, Suspense } from 'react';
import { Routes, Route, useLocation, useNavigate, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useShareMeta from '../hooks/useShareMeta';
import AppShell from '../components/AppShell';
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
import Settings from './Settings.jsx';
import DemographicsForm from './DemographicsForm.jsx';
import History from './History.jsx';
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion';
import Login from './Login.jsx';
import QuizStart from './QuizStart.jsx';
import QuizPlay from './QuizPlay.jsx';
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


// Survey component moved to SurveyPage.jsx

const Result = () => {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const iqParam = params.get('iq');
  const percentileParam = params.get('percentile');
  const shareParam = params.get('share_url');
  const share = shareParam && shareParam !== 'null' ? shareParam : null;
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
    score: Number(score).toFixed(2),
    percentile: Number(percentile).toFixed(1)
  });

  return (
    <PageTransition>
      <AppShell>
        <section data-b-spec="result-v1" className="max-w-md mx-auto space-y-8 text-center">
          <Card className="space-y-4">
            <div>
              <div className="text-5xl font-bold">{Number.isFinite(score) ? score.toFixed(2) : 'N/A'}</div>
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
        <Route path="/quiz/start" element={<RequireAuth><QuizStart /></RequireAuth>} />
        <Route path="/quiz/play" element={<RequireAuth><QuizPlay /></RequireAuth>} />
        <Route path="/quiz" element={<Navigate to="/quiz/start" replace />} />
        <Route path="/test" element={<Navigate to="/quiz/start" replace />} />
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
        <Route path="/country" element={<RequireAuth><SelectNationality /></RequireAuth>} />
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
