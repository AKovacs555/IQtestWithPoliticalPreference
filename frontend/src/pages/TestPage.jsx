import React from 'react';
import { useTranslation } from 'react-i18next';
import Layout from '../components/Layout';
import { getQuizStart, submitQuiz } from '../api';
import ProgressBar from '../components/ProgressBar';
import QuestionCard from '../components/QuestionCard';
import { motion } from 'framer-motion';

const PageTransition = ({ children }) => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
    {children}
  </motion.div>
);

export default function TestPage() {
  const [session, setSession] = React.useState(null);
  const [questions, setQuestions] = React.useState([]);
  const [answers, setAnswers] = React.useState([]);
  const [current, setCurrent] = React.useState(0);
  const [timeLeft, setTimeLeft] = React.useState(300);
  const [suspicious, setSuspicious] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const { t, i18n } = useTranslation();
  const watermark = React.useMemo(() => `${session?.slice(0,6) || ''}-${Date.now()}`,[session]);

  React.useEffect(() => {
    async function load() {
      try {
        const data = await getQuizStart(undefined, i18n.language);
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
  }, []);

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
    const t = setInterval(() => setTimeLeft(s => Math.max(s - 1, 0)), 1000);
    return () => clearInterval(t);
  }, []);

  React.useEffect(() => {
    if (timeLeft === 0 && !loading && !error) {
      (async () => {
        const result = await submitQuiz(
          session,
          answers.map((ans, idx) => ({ id: questions[idx].id, answer: ans ?? -1 }))
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
}
