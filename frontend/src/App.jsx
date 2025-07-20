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
  const [questions, setQuestions] = React.useState([]);
  const [index, setIndex] = React.useState(0);
  const [answers, setAnswers] = React.useState([]);
  const [timeLeft, setTimeLeft] = React.useState(360);

  React.useEffect(() => {
    fetch('/quiz/start')
      .then(res => res.json())
      .then(data => setQuestions(data.questions));
  }, []);

  React.useEffect(() => {
    const t = setInterval(() => setTimeLeft(t => Math.max(t - 1, 0)), 1000);
    return () => clearInterval(t);
  }, []);

  const current = questions[index];

  const select = (i) => {
    setAnswers([...answers, { id: current.id, answer: i }]);
    if (index + 1 < questions.length) {
      setIndex(index + 1);
    } else {
      fetch('/quiz/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: [...answers, { id: current.id, answer: i }] })
      })
        .then(res => res.json())
        .then(() => window.location.href = '/result');
    }
  };

  return (
    <PageTransition>
      <div className="p-4 space-y-4">
        <div className="h-2 bg-gray-200 rounded">
          <div
            className="h-2 bg-blue-600 rounded"
            style={{ width: `${(index / 20) * 100}%` }}
          />
        </div>
        <div className="text-right">{Math.floor(timeLeft / 60)}:{`${timeLeft % 60}`.padStart(2, '0')}</div>
        {current && (
          <div>
            <p className="font-semibold mb-2">{current.question}</p>
            {current.options.map((opt, i) => (
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

const Result = () => (
  <PageTransition>
    <div className="p-4">Result page.</div>
  </PageTransition>
);

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
