import React, { useEffect, useState } from 'react';
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useShareMeta from '../hooks/useShareMeta';
import Layout from '../components/Layout';
import AdminQuestions from './AdminQuestions';
import AdminSurvey from './AdminSurvey';
import AdminUsers from './AdminUsers';
import ProgressBar from '../components/ProgressBar';
import Home from './Home';
import Pricing from './Pricing';
import Leaderboard from './Leaderboard';
import SelectSet from './SelectSet';
import PartySelect from './PartySelect';
import SelectNationality from './SelectNationality';
import SelectParty from './SelectParty';
import SurveyPage from './SurveyPage';
import Dashboard from './Dashboard';
import { Chart } from 'chart.js/auto';
import QuestionCard from '../components/QuestionCard';
import Settings from './Settings.jsx';
import DemographicsForm from './DemographicsForm.jsx';
import History from './History.jsx';
import confetti from 'canvas-confetti';
import { getQuizStart, submitQuiz } from '../api';
import TestPage from './TestPage.jsx';
import { AnimatePresence, motion } from 'framer-motion';
import SignupPage from './SignupPage.jsx';
import LoginPage from './LoginPage.jsx';

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
  const { t } = useTranslation();
  const navigate = useNavigate();
  const watermark = React.useMemo(() => `${session?.slice(0,6) || ''}-${Date.now()}`,[session]);

  React.useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
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
    async function load() {
      try {
        const uid = localStorage.getItem('user_id');
        const data = await getQuizStart(setId, undefined, uid);
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
  }, [setId, navigate]);

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

  React.useEffect(() => {
    if (timeLeft === 0 && !loading && !error) {
      (async () => {
        const result = await submitQuiz(
          session,
          answers.map((ans, idx) => ({
            id: questions[idx].id,
            answer: ans ?? -1,
          })),
          localStorage.getItem('user_id')
        );
        const params = new URLSearchParams({
          score: result.iq,
          percentile: result.percentile,
          share: result.share_url,
        });
        navigate('/result?' + params.toString());
      })();
    }
  }, [timeLeft, loading, error, navigate]);

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
    const a = [...answers];
    a[current] = i;
    setAnswers(a);
    if (current + 1 < questions.length) {
      setCurrent(c => c + 1);
    } else {
      try {
        const data = await submitQuiz(
          session,
          a.map((ans, idx) => ({ id: questions[idx].id, answer: ans })),
          localStorage.getItem('user_id')
        );
        const params = new URLSearchParams({
          score: data.iq,
          percentile: data.percentile,
          share: data.share_url,
        });
        navigate('/result?' + params.toString());
      } catch (err) {
        setError(err.message);
      }
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
  const params = new URLSearchParams(window.location.search);
  const score = params.get('score');
  const percentile = params.get('percentile');
  const share = params.get('share');
  const ref = React.useRef();
  const [avg, setAvg] = React.useState(null);
  const { t } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    confetti({ particleCount: 150, spread: 70 });
  }, []);

  useShareMeta(share);

  useEffect(() => {
    const ctx = ref.current.getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['IQ'],
        datasets: [{ data: [score], backgroundColor: 'rgb(75,192,192)' }]
      },
      options: { scales: { y: { beginAtZero: true } } }
    });
  }, []);

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
          <p>IQ: {Number(score).toFixed(2)}</p>
          <p>Percentile: {Number(percentile).toFixed(1)}%</p>
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
          <div className="mt-4">
            <a
              href="/premium.html"
              className="px-4 py-2 rounded-md bg-primary text-white text-sm hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary"
            >
              Upgrade to Pro Pass
            </a>
          </div>
          <p className="text-sm text-gray-600">This test is for research and entertainment.</p>
        </div>
      </Layout>
    </PageTransition>
  );
};

export default function App() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home />} />
        <Route path="/select-set" element={<SelectSet />} />
        <Route path="/start" element={<DemographicsForm />} />
        <Route path="/quiz" element={<Quiz />} />
        <Route path="/test" element={<TestPage />} />
        <Route path="/survey" element={<SurveyPage />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/result" element={<Result />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings/:userId" element={<Settings />} />
        <Route path="/history/:userId" element={<History />} />
        <Route path="/party" element={<PartySelect />} />
        <Route path="/select-nationality" element={<SelectNationality />} />
        <Route path="/select-party" element={<SelectParty />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/admin/questions" element={<AdminQuestions />} />
        <Route path="/admin/surveys" element={<AdminSurvey />} />
        <Route path="/admin/users" element={<AdminUsers />} />
      </Routes>
    </AnimatePresence>
  );
}
