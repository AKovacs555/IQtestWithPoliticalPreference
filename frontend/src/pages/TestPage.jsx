import React from 'react';
import { useTranslation } from 'react-i18next';
import Layout from '../components/Layout';
import { getQuizStart, submitQuiz } from '../api';
import ProgressBar from '../components/ProgressBar';
import QuestionCard from '../components/QuestionCard';
import { useNavigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function TestPage() {
  const [session, setSession] = React.useState(null);
  const [questions, setQuestions] = React.useState([]);
  const [answers, setAnswers] = React.useState([]);
  const [current, setCurrent] = React.useState(0);
  const [timeLeft, setTimeLeft] = React.useState(300);
  const [suspicious, setSuspicious] = React.useState(false);
  const [blackout, setBlackout] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isMobile = /Mobi|Android/i.test(navigator.userAgent);
  const watermark = React.useMemo(() => `${session?.slice(0,6) || ''}-${Date.now()}`,[session]);

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
    async function load() {
      try {
        const data = await getQuizStart(undefined, i18n.language);
        setSession(data.session_id);
        setQuestions(data.questions);
        setCurrent(0);
      } catch (err) {
        if (err.message && err.message.includes('survey_required')) {
          navigate('/survey');
          return;
        }
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [i18n.language, navigate, user]);

  React.useEffect(() => {
    if (
      questions.length > 0 &&
      !isMobile &&
      document.fullscreenElement == null
    ) {
      document.documentElement.requestFullscreen().catch(() => {});
    }
  }, [questions.length, isMobile]);

  React.useEffect(() => {
    const handleFs = () => {
      if (document.fullscreenElement == null) setBlackout(true);
    };
    document.addEventListener('fullscreenchange', handleFs);
    return () => document.removeEventListener('fullscreenchange', handleFs);
  }, []);

  React.useEffect(() => {
    const handleVis = () => {
      if (document.visibilityState === 'hidden') setBlackout(true);
    };
    document.addEventListener('visibilitychange', handleVis);
    return () => document.removeEventListener('visibilitychange', handleVis);
  }, []);

  React.useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'PrintScreen') setBlackout(true);
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
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
        navigate('/result?' + params.toString());
      } catch (err) {
        setError(err.message);
      }
    }
  };

  return (
    <Layout>
      <div
        className="watermark fixed inset-0 pointer-events-none opacity-10 text-xs z-40 flex items-end justify-end p-2 select-none"
      >
        {session && `${session.slice(0,6)} ${new Date().toLocaleString()}`}
      </div>
      {blackout && (
        <div className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center text-white text-center z-50">
          {t('warning.screenshot_detected')}
        </div>
      )}
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
  );
}
