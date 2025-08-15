import React from 'react';
import { useTranslation } from 'react-i18next';
import AppShell from '../components/AppShell';
import { getQuizStart, submitQuiz, abandonQuiz } from '../api';
import { AnimatePresence, motion, MotionConfig } from 'framer-motion';
import QuestionCard from '../components/QuestionCard';
import { useNavigate } from 'react-router-dom';
import { Clock } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Progress from '../components/ui/Progress';
import Button from '../components/ui/Button';

export default function TestPage() {
  const [session, setSession] = React.useState(null);
  const [questions, setQuestions] = React.useState([]);
  const [answers, setAnswers] = React.useState([]);
  const [current, setCurrent] = React.useState(0);
  const DURATION = parseInt(import.meta.env.VITE_QUIZ_DURATION_MINUTES || '25', 10) * 60;
  const [timeLeft, setTimeLeft] = React.useState(DURATION);
  const [suspicious, setSuspicious] = React.useState(false);
  const [blackout, setBlackout] = React.useState(false);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [submitting, setSubmitting] = React.useState(false);
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const isMobile = /Mobi|Android/i.test(navigator.userAgent);
  const watermark = React.useMemo(() => `${session?.slice(0,6) || ''}-${Date.now()}`,[session]);

  React.useEffect(() => {
    // 事前条件の確認
    const status = sessionStorage.getItem('quiz_status');
    const exp = sessionStorage.getItem('quiz_expires');
    if (status && status !== 'started') {
      navigate('/result');
      return;
    }
    if (exp && Date.now() > Date.parse(exp)) {
      navigate('/result');
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
        const data = await getQuizStart(undefined, i18n.language);
        setSession(data.session_id);
        setQuestions(data.questions);
        setCurrent(0);
        sessionStorage.setItem('quiz_session', data.session_id);
        if (data.expires_at) {
          sessionStorage.setItem('quiz_expires', data.expires_at);
          const secs = Math.floor((new Date(data.expires_at) - Date.now()) / 1000);
          setTimeLeft(secs > 0 ? secs : 0);
        }
        sessionStorage.setItem('quiz_status', 'started');
      } catch (err) {
        if (err.code === 'demographic_required') {
          navigate('/demographics');
          return;
        }
        if (err.code === 'survey_required') {
          navigate('/survey');
          return;
        }
        if (err.code === 'nationality_required') {
          navigate('/select-nationality');
          return;
        }
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [i18n.language, navigate]);

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

  const submit = async (list) => {
    if (submitting) return;
    setSubmitting(true);
    try {
      // console.log('submitQuiz called');
      const result = await submitQuiz(session, list);
      sessionStorage.setItem('quiz_status', 'submitted');
      sessionStorage.removeItem('quiz_session');
      sessionStorage.removeItem('quiz_expires');
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
          answers.map((ans, idx) => ({ id: questions[idx].id, answer: ans ?? -1 }))
        );
      })();
    }
  }, [timeLeft, loading, error]);

  React.useEffect(() => {
    const handleExit = () => {
      const sid = sessionStorage.getItem('quiz_session');
      if (sid) abandonQuiz(sid);
    };
    window.addEventListener('beforeunload', handleExit);
    const vis = () => {
      if (document.visibilityState === 'hidden') handleExit();
    };
    document.addEventListener('visibilitychange', vis);
    return () => {
      window.removeEventListener('beforeunload', handleExit);
      document.removeEventListener('visibilitychange', vis);
    };
  }, []);

  React.useEffect(() => {
    const handlePop = () => {
      window.history.pushState(null, '', window.location.href);
    };
    window.history.pushState(null, '', window.location.href);
    window.addEventListener('popstate', handlePop);
    return () => window.removeEventListener('popstate', handlePop);
  }, []);

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
    <AppShell>
      {blackout && (
        <div className="fixed inset-0 glass-card bg-black/80 text-white flex items-center justify-center text-center z-50">
          {t('warning.screenshot_detected')}
        </div>
      )}
      <div
        className="watermark fixed inset-0 pointer-events-none opacity-10 text-xs z-40 flex items-end justify-end p-2 select-none"
      >
        {session && `${session.slice(0,6)} ${new Date().toLocaleString()}`}
      </div>
      <div data-b-spec="quiz-v1" className="space-y-6 max-w-xl mx-auto quiz-container mt-4">
        {loading && <p>Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}
        {!loading && !error && (
          <>
            <div className="flex items-center justify-between">
              <Button variant="ghost" className="px-0" onClick={() => navigate('/dashboard')}>← {t('dashboard.title', { defaultValue: 'Dashboard' })}</Button>
              <Badge variant="outline">IQ Test</Badge>
              <div className="flex items-center gap-1 font-mono">
                <Clock className="w-4 h-4" />
                {Math.floor(timeLeft / 60)}:{`${timeLeft % 60}`.padStart(2, '0')}
              </div>
            </div>
            <Card className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{t('quiz.progress', { current: current + 1, total: questions.length })}</span>
                <span>{Math.round((current / questions.length) * 100)}%</span>
              </div>
              <Progress value={(current / questions.length) * 100} />
            </Card>
            <MotionConfig reducedMotion="user">
              <AnimatePresence mode="wait">
                <motion.div
                  key={questions[current]?.id || current}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.18 }}
                >
                  {questions[current] && (
                    <QuestionCard
                      question={questions[current]}
                      onSelect={select}
                      watermark={watermark}
                      disabled={submitting}
                    />
                  )}
                </motion.div>
              </AnimatePresence>
            </MotionConfig>
          </>
        )}
        {suspicious && (
          <p className="text-red-600 text-sm">Session flagged for leaving the page.</p>
        )}
      </div>
    </AppShell>
  );
}
