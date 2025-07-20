import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';

const PageTransition = ({ children }) => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
    {children}
  </motion.div>
);

const Home = () => (
  <PageTransition>
    <div className="p-4 text-center">
      <h1 className="text-2xl font-bold mb-4">IQ Test</h1>
      <Link to="/quiz" className="bg-blue-600 text-white px-4 py-2 rounded">Start Quiz</Link>
    </div>
  </PageTransition>
);

const Quiz = () => {
  const [session, setSession] = React.useState(null);
  const [question, setQuestion] = React.useState(null);
  const [count, setCount] = React.useState(0);
  const [timeLeft, setTimeLeft] = React.useState(360);

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

  const select = (i) => {
    fetch('/adaptive/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: session, answer: i })
    })
      .then(res => res.json())
      .then(data => {
        if (data.finished) {
          const params = new URLSearchParams({ score: data.score, percentile: data.percentile });
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
          <div>
            <p className="font-semibold mb-2">{question.question}</p>
            {question.options.map((opt, i) => (
              <button
                key={i}
                onClick={() => select(i)}
                className="block w-full mb-2 p-2 border rounded"
              >
                {opt}
              </button>
            ))}
          </div>
        )}
      </div>
    </PageTransition>
  );
};

const Result = () => {
  const params = new URLSearchParams(window.location.search);
  const score = params.get('score');
  const percentile = params.get('percentile');
  return (
    <PageTransition>
      <div className="p-4 text-center space-y-2">
        <h2 className="text-xl font-bold">Your Results</h2>
        <p>Ability score: {Number(score).toFixed(2)}</p>
        <p>Percentile: {Number(percentile).toFixed(1)}%</p>
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
        <Route path="/quiz" element={<Quiz />} />
        <Route path="/result" element={<Result />} />
      </Routes>
    </AnimatePresence>
  );
}
