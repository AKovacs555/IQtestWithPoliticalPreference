import React, { useEffect, useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Chart } from 'chart.js/auto';
import QuestionCanvas from './QuestionCanvas';
import Settings from './Settings.jsx';
import DemographicsForm from './DemographicsForm.jsx';

const PageTransition = ({ children }) => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
    {children}
  </motion.div>
);

const Home = () => (
  <PageTransition>
    <div className="p-4 text-center space-y-2">
      <h1 className="text-2xl font-bold mb-4">IQ Test</h1>
      <Link to="/start" className="btn btn-primary">Start Quiz</Link>
      <div>
        <Link to="/survey" className="underline text-sm">Political Survey</Link>
      </div>
      <div className="text-sm mt-2">
        <Link to="/settings/testuser" className="underline">View Settings</Link>
      </div>
    </div>
  </PageTransition>
);

const Quiz = () => {
  const [session, setSession] = React.useState(null);
  const [question, setQuestion] = React.useState(null);
  const [count, setCount] = React.useState(0);
  const [timeLeft, setTimeLeft] = React.useState(360);
  const [suspicious, setSuspicious] = React.useState(false);
  const watermark = React.useMemo(() => `${session?.slice(0,6) || ''}-${Date.now()}`,[session]);

  React.useEffect(() => {
    fetch('/adaptive/start')
      .then(res => res.json())
      .then(data => {
        setSession(data.session_id);
        setQuestion(data.question);
      });
  }, []);

  React.useEffect(() => {
    const t = setInterval(() => setTimeLeft(t => Math.max(t - 1, 0)), 1000);
    return () => clearInterval(t);
  }, []);

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

  const select = (i) => {
    fetch('/adaptive/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: session, answer: i })
    })
      .then(res => res.json())
      .then(data => {
        if (data.finished) {
          const params = new URLSearchParams({
            score: data.score,
            percentile: data.percentile,
            share: data.share_url,
          });
          window.location.href = '/result?' + params.toString();
        } else {
          setQuestion(data.next_question);
          setCount(c => c + 1);
        }
      });
  };

  return (
    <PageTransition>
      <div className="p-4 space-y-4">
        <div className="h-2 bg-gray-200 rounded">
          <div
            className="h-2 bg-blue-600 rounded"
            style={{ width: `${(count / 20) * 100}%` }}
          />
        </div>
        <div className="text-right">{Math.floor(timeLeft / 60)}:{`${timeLeft % 60}`.padStart(2, '0')}</div>
        {question && (
          <QuestionCanvas
            question={question.question}
            options={question.options}
            onSelect={select}
            watermark={watermark}
          />
        )}
        {suspicious && (
          <p className="text-red-600 text-sm">Session flagged for leaving the page.</p>
        )}
      </div>
    </PageTransition>
  );
};

const Survey = () => {
  const [items, setItems] = useState([]);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState([]);

  useEffect(() => {
    fetch('/survey/start').then(res => res.json()).then(data => setItems(data.items));
  }, []);

  const back = () => setIndex(i => Math.max(i - 1, 0));
  const next = (v) => {
    const a = [...answers];
    a[index] = { id: items[index].id, value: v };
    setAnswers(a);
    if (index + 1 < items.length) {
      setIndex(index + 1);
    } else {
      fetch('/survey/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: a })
      })
        .then(res => res.json())
        .then(data => {
          const params = new URLSearchParams({
            lr: data.left_right,
            auth: data.libertarian_authoritarian,
            cat: data.category,
            desc: data.description
          });
          window.location.href = '/survey-result?' + params.toString();
        });
    }
  };

  const item = items[index];
  return (
    <PageTransition>
      <div className="p-4 space-y-4">
        <div className="h-2 bg-gray-200 rounded">
          <div className="h-2 bg-green-600 rounded" style={{ width: `${(index / items.length) * 100}%` }} />
        </div>
        {item && (
          <div>
            <p className="mb-2 font-semibold">{item.statement}</p>
            <div className="space-y-2">
              {[1,2,3,4,5].map(v => (
                <button key={v} onClick={() => next(v)} className="w-full p-2 border rounded">
                  {v}
                </button>
              ))}
            </div>
            {index > 0 && <button onClick={back} className="mt-2 underline text-sm">Back</button>}
          </div>
        )}
      </div>
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
      <div className="p-4 text-center space-y-2">
        <h2 className="text-xl font-bold">{cat}</h2>
        <p>{desc}</p>
        <canvas id="chart" height="200"></canvas>
        <Link to="/" className="underline">Home</Link>
      </div>
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
    fetch('/leaderboard')
      .then(res => res.json())
      .then(data => {
        const all = data.leaderboard.map(l => l.avg_iq);
        if (all.length) setAvg(all.reduce((a,b) => a+b,0)/all.length);
      });
  }, []);
  React.useEffect(() => {
    if (!share) return;
    const og = document.querySelector('meta[property="og:image"]') || document.createElement('meta');
    og.setAttribute('property', 'og:image');
    og.content = share;
    document.head.appendChild(og);
    const tw = document.querySelector('meta[name="twitter:image"]') || document.createElement('meta');
    tw.setAttribute('name', 'twitter:image');
    tw.content = share;
    document.head.appendChild(tw);
  }, [share]);

  const url = encodeURIComponent(window.location.href);
  const text = encodeURIComponent(`I scored ${Number(score).toFixed(1)} IQ!`);

  return (
    <PageTransition>
      <div className="p-4 text-center space-y-2">
        <h2 className="text-xl font-bold">Your Results</h2>
        <p>IQ: {Number(score).toFixed(2)}</p>
        <p>Percentile: {Number(percentile).toFixed(1)}%</p>
        <span className="text-xs text-gray-500" title="Scores are for entertainment and may not reflect a clinical IQ">what's this?</span>
        {avg && <p className="text-sm">Overall average IQ: {avg.toFixed(1)}</p>}
        <canvas ref={ref} height="120"></canvas>
        {share && (
          <div className="space-x-2">
            <a href={`https://twitter.com/intent/tweet?url=${url}&text=${text}`} target="_blank" rel="noreferrer" className="btn btn-sm">Share on X</a>
            <a href={`https://social-plugins.line.me/lineit/share?url=${url}`} target="_blank" rel="noreferrer" className="btn btn-sm">LINE</a>
          </div>
        )}
        <p className="text-sm text-gray-600">This test is for research and entertainment.</p>
        <Link to="/" className="underline">Home</Link>
      </div>
    </PageTransition>
  );
};

export default function App() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Home />} />
        <Route path="/start" element={<DemographicsForm />} />
        <Route path="/quiz" element={<Quiz />} />
        <Route path="/survey" element={<Survey />} />
        <Route path="/survey-result" element={<SurveyResult />} />
        <Route path="/result" element={<Result />} />
        <Route path="/settings/:userId" element={<Settings />} />
      </Routes>
    </AnimatePresence>
  );
}
