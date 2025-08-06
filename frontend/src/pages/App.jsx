import React, { useEffect, useState } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useShareMeta from '../hooks/useShareMeta';
import useAuth from '../hooks/useAuth';
import Layout from '../components/Layout';
import AdminQuestions from './AdminQuestions';
import AdminSurvey from './AdminSurvey';
import AdminUsers from './AdminUsers';
import AdminSets from './AdminSets';
import AdminSettings from './AdminSettings.jsx';
import AdminQuestionStats from './AdminQuestionStats.jsx';
import ProgressBar from '../components/ProgressBar';
import Home from './Home';
import Pricing from './Pricing';
import Leaderboard from './Leaderboard';
import SelectSet from './SelectSet';
import SelectNationality from './SelectNationality';
import SurveyPage from './SurveyPage';
import Dashboard from './Dashboard';
import Chart from 'chart.js/auto';
import QuestionCard from '../components/QuestionCard';
import Settings from './Settings.jsx';
import DemographicsForm from './DemographicsForm.jsx';
import History from './History.jsx';
import confetti from 'canvas-confetti';
import { getQuizStart, submitQuiz } from '../api';
import { AnimatePresence, motion } from 'framer-motion';
import SignupPage from './SignupPage.jsx';
import LoginPage from './LoginPage.jsx';
import TestPage from './TestPage.jsx';
const API_BASE = import.meta.env.VITE_API_BASE || "";

const PageTransition = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    transition={{ duration: 0.2 }}
  >
    {children}
  </motion.div>
);


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
    if (localStorage.getItem('survey_completed') !== 'true') {
      navigate('/survey');
      return;
    }
    if (localStorage.getItem('demographic_completed') !== 'true') {
      navigate('/demographics');
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
      <Layout>
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
      </Layout>
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
  const ref = React.useRef();
  const [avg, setAvg] = React.useState(null);
  const { t } = useTranslation();
  const price = import.meta.env.VITE_PRO_PRICE_MONTHLY;
  const navigate = useNavigate();

  useEffect(() => {
    confetti({ particleCount: 150, spread: 70 });
  }, []);

  useShareMeta(share);

  useEffect(() => {
    if (!ref.current || !Number.isFinite(score)) return;
    const ctx = ref.current.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['IQ'],
        datasets: [{ data: [score], backgroundColor: 'rgb(75,192,192)' }],
      },
      options: { scales: { y: { beginAtZero: true } } },
    });
  }, [score]);

  useEffect(() => {
    fetch(`${API_BASE}/leaderboard`)
      .then(res => res.json())
      .then(data => {
        const all = data.leaderboard.map(l => l.avg_iq);
        if (all.length) setAvg(all.reduce((a,b) => a+b,0)/all.length);
      });
  }, []);

  const url = encodeURIComponent(window.location.href);
  const text = encodeURIComponent(
    t('result.share_text', {
      score: Number(score).toFixed(1),
      percentile: Number(percentile).toFixed(1)
    })
  );

  return (
    <PageTransition>
      <Layout>
        <div className="text-center space-y-4 p-6 max-w-md mx-auto rounded-2xl backdrop-blur-md bg-white/60 shadow-lg">
          <h2 className="text-2xl font-bold">Your Results</h2>
          <p>IQ: {Number.isFinite(score) ? score.toFixed(2) : 'N/A'}</p>
          <p>Percentile: {Number.isFinite(percentile) ? percentile.toFixed(1) : 'N/A'}%</p>
          <span className="text-xs text-gray-500" title="Scores are for entertainment and may not reflect a clinical IQ">what's this?</span>
          {avg && <p className="text-sm">Overall average IQ: {avg.toFixed(1)}</p>}
          <canvas ref={ref} height="120"></canvas>
          {share && <img src={share} alt="IQ share card" className="mx-auto rounded" />}
          {share && (
            <div className="space-x-2">
              {/* Share on X (Twitter) */}
              <a
                href={`https://twitter.com/intent/tweet?url=${url}&text=${text}`}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 rounded-md bg-primary text-white text-sm hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                X
              </a>
              {/* Share on LINE */}
              <a
                href={`https://social-plugins.line.me/lineit/share?url=${url}`}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 rounded-md bg-primary text-white text-sm hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                LINE
              </a>
              {/* Copy link or share */}
              <button
                onClick={() => {
                  if (navigator.share) {
                    navigator.share({ url: window.location.href, text: decodeURIComponent(text) });
                  } else {
                    navigator.clipboard.writeText(window.location.href);
                    alert(t('result.link_copied'));
                  }
                }}
                className="px-4 py-2 rounded-md bg-primary text-white text-sm hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {t('result.share')}
              </button>
            </div>
          )}
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 mt-4 rounded-md bg-primary text-white text-sm hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary"
          >
            {t('result.back_to_home')}
          </button>
          <div className="mt-4 space-y-2">
            <p>{t('result.pro_prompt', { price })}</p>
            <a
              href="/pricing"
              className="px-4 py-2 rounded-md bg-primary text-white text-sm hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {t('pricing.subscribe')}
            </a>
          </div>
          <p className="text-sm text-gray-600">This test is for research and entertainment.</p>
        </div>
      </Layout>
    </PageTransition>
  );
};

export default function App() {
  // Admin routes should always be registered when the build enables them.
  // Individual pages handle permission checks and show an access message
  // when a non-admin visits the route. Previously, admin routes were only
  // added when `user?.is_admin` was truthy which resulted in a blank page
  // if a non-admin attempted to access an `/admin/*` path directly. By
  // removing the user check here, the routes exist for everyone and the
  // components can render an informative error instead of nothing.
  const showAdmin = import.meta.env.VITE_SHOW_ADMIN === 'true' || import.meta.env.DEV;
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home />} />
        <Route path="/select-set" element={<SelectSet />} />
        <Route path="/demographics" element={<DemographicsForm />} />
        <Route path="/quiz" element={<TestPage />} />
        <Route path="/test" element={<TestPage />} />
        <Route path="/survey" element={<SurveyPage />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/result" element={<Result />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/settings/:userId" element={<Settings />} />
          <Route path="/history/:userId" element={<History />} />
          <Route path="/select-nationality" element={<SelectNationality />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/login" element={<LoginPage />} />
        {showAdmin && (<><Route path="/admin/questions" element={<AdminQuestions />} />
        <Route path="/admin/question-stats" element={<AdminQuestionStats />} />
        <Route path="/admin/surveys" element={<AdminSurvey />} />
        <Route path="/admin/users" element={<AdminUsers />} />
        <Route path="/admin/sets" element={<AdminSets />} />
        <Route path="/admin/settings" element={<AdminSettings />} /></>)}
      </Routes>
    </AnimatePresence>
  );
}
