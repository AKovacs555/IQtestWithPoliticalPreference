import React, { useEffect, useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useShareMeta from '../hooks/useShareMeta';
import { AnimatePresence, motion } from 'framer-motion';
import Layout from '../components/Layout';
import AdminUpload from './AdminUpload';
import AdminQuestions from './AdminQuestions';
import ProgressBar from '../components/ProgressBar';
import Home from './Home';
import Pricing from './Pricing';
import Leaderboard from './Leaderboard';
import SelectSet from './SelectSet';
import PartySelect from './PartySelect';
import { Chart } from 'chart.js/auto';
import QuestionCard from '../components/QuestionCard';
import Settings from './Settings.jsx';
import DemographicsForm from './DemographicsForm.jsx';
import History from './History.jsx';
import confetti from 'canvas-confetti';
import { getQuizStart, submitQuiz, getSurvey, submitSurvey } from '../api';

const PageTransition = ({ children }) => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
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
  const watermark = React.useMemo(() => `${session?.slice(0,6) || ''}-${Date.now()}`,[session]);

  React.useEffect(() => {
    async function load() {
      try {
        const data = await getQuizStart(setId);
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
  }, [setId]);

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
          }))
        );
        const params = new URLSearchParams({
          score: result.iq,
          percentile: result.percentile,
          share: result.share_url,
        });
        window.location.href = '/result?' + params.toString();
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
    const a = [...answers];
    a[current] = i;
    setAnswers(a);
    if (current + 1 < questions.length) {
      setCurrent(c => c + 1);
    } else {
      try {
        const data = await submitQuiz(
          session,
          a.map((ans, idx) => ({ id: questions[idx].id, answer: ans }))
        );
        const params = new URLSearchParams({
          score: data.iq,
          percentile: data.percentile,
          share: data.share_url,
        });
        window.location.href = '/result?' + params.toString();
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
          {error && <p className="text-error">{error}</p>}
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
            <p className="text-error text-sm">Session flagged for leaving the page.</p>
          )}
        </div>
      </Layout>
    </PageTransition>
  );
};

const Survey = () => {
  const [items, setItems] = useState([]);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getSurvey();
        setItems(data.items);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const back = () => setIndex(i => Math.max(i - 1, 0));
  const next = async (v) => {
    const a = [...answers];
    a[index] = { id: items[index].id, value: v };
    setAnswers(a);
    if (index + 1 < items.length) {
      setIndex(index + 1);
    } else {
      try {
        const data = await submitSurvey(a);
        const params = new URLSearchParams({
          lr: data.left_right,
          auth: data.libertarian_authoritarian,
          cat: data.category,
          desc: data.description,
        });
        window.location.href = '/survey-result?' + params.toString();
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const item = items[index];
  return (
    <PageTransition>
      <Layout>
        <div className="space-y-4 max-w-lg mx-auto">
          {loading && <p>Loading...</p>}
          {error && <p className="text-error">{error}</p>}
          {!loading && item && (
            <div className="card bg-base-100 shadow-md p-4 space-y-2">
              <p className="mb-2 font-semibold">{item.statement}</p>
              <div className="grid grid-cols-5 gap-2">
                {[1,2,3,4,5].map(v => (
                  <button key={v} onClick={() => next(v)} className="btn btn-primary">
                    {v}
                  </button>
                ))}
              </div>
              {index > 0 && <button onClick={back} className="mt-2 underline text-sm">Back</button>}
            </div>
          )}
          {!loading && <ProgressBar value={(index / items.length) * 100} />}
        </div>
      </Layout>
    </PageTransition>
  );
};

const SurveyResult = () => {
  const params = new URLSearchParams(window.location.search);
  const lr = parseFloat(params.get('lr'));
  const auth = parseFloat(params.get('auth'));
  const cat = params.get('cat');
  const desc = params.get('desc');

  useEffect(() => {
    const ctx = document.getElementById('chart');
    new Chart(ctx, {
      type: 'radar',
      data: {
        labels: ['Left/Right', 'Libertarian/Authoritarian'],
        datasets: [{
          data: [lr, auth],
          backgroundColor: 'rgba(54,162,235,0.2)',
          borderColor: 'rgb(54,162,235)'
        }]
      },
      options: { scales: { r: { min: -1, max: 1 } } }
    });
  }, []);

  return (
    <PageTransition>
      <Layout>
        <div className="text-center space-y-2">
          <h2 className="text-xl font-bold">{cat}</h2>
          <p>{desc}</p>
          <canvas id="chart" height="200"></canvas>
          <Link to="/" className="underline">Home</Link>
        </div>
      </Layout>
    </PageTransition>
  );
};

const Result = () => {
  const params = new URLSearchParams(window.location.search);
  const score = params.get('score');
  const percentile = params.get('percentile');
  const share = params.get('share');
  const ref = React.useRef();
  const [avg, setAvg] = React.useState(null);
  const [partyName, setPartyName] = React.useState('');
  const { t } = useTranslation();

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

  useEffect(() => {
    const uid = localStorage.getItem('user_id') || 'testuser';
    Promise.all([
      fetch(`${API_BASE}/survey/start`).then(r => r.json()),
      fetch(`${API_BASE}/user/stats/${uid}`).then(r => r.ok ? r.json() : { party_log: [] })
    ]).then(([p, s]) => {
      const latest = s.party_log && s.party_log.length ? s.party_log[s.party_log.length-1].party_ids[0] : null;
      if (latest != null) {
        const map = {};
        p.parties.forEach(pt => { map[pt.id] = pt.name; });
        setPartyName(map[latest] || '');
      }
    });
  }, []);

  const url = encodeURIComponent(window.location.href);
  const text = encodeURIComponent(
    `I scored ${Number(score).toFixed(1)} IQ! ${partyName ? 'Supporter of ' + partyName : ''}`
  );

  return (
    <PageTransition>
      <Layout>
        <div className="text-center space-y-2">
          <h2 className="text-xl font-bold">Your Results</h2>
          <p>IQ: {Number(score).toFixed(2)}</p>
          <p>Percentile: {Number(percentile).toFixed(1)}%</p>
          <span className="text-xs text-gray-500" title="Scores are for entertainment and may not reflect a clinical IQ">what's this?</span>
          {avg && <p className="text-sm">Overall average IQ: {avg.toFixed(1)}</p>}
          <canvas ref={ref} height="120"></canvas>
          {share && <img src={share} alt="IQ share card" className="mx-auto rounded" />}
          {share && (
            <div className="space-x-2">
              <a href={`https://twitter.com/intent/tweet?url=${url}&text=${text}`} target="_blank" rel="noreferrer" className="btn btn-sm">Share on X</a>
              <a href={`https://social-plugins.line.me/lineit/share?url=${url}`} target="_blank" rel="noreferrer" className="btn btn-sm">LINE</a>
              {navigator.share && (
                <button onClick={() => navigator.share({ url, text })} className="btn btn-sm">{t('share.button')}</button>
              )}
            </div>
          )}
          <div className="mt-4">
            <a href="/premium.html" className="btn btn-primary btn-sm">Upgrade to Pro Pass</a>
          </div>
          <p className="text-sm text-gray-600">This test is for research and entertainment.</p>
          <Link to="/" className="underline">Home</Link>
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
        <Route path="/survey" element={<Survey />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/survey-result" element={<SurveyResult />} />
        <Route path="/result" element={<Result />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/settings/:userId" element={<Settings />} />
        <Route path="/history/:userId" element={<History />} />
        <Route path="/party" element={<PartySelect />} />
        <Route path="/admin/upload" element={<AdminUpload />} />
        <Route path="/admin/questions" element={<AdminQuestions />} />
      </Routes>
    </AnimatePresence>
  );
}
