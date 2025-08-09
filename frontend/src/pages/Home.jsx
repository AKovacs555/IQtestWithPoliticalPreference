import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import useAuth from '../hooks/useAuth';

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function Home() {
  const { t } = useTranslation();
  const userId = localStorage.getItem('user_id') || '';
  const { user } = useAuth();
  const navigate = useNavigate();
  const [freeStats, setFreeStats] = useState(null);
  const handleStart = () => {
    if (!user) {
      navigate('/login');
    } else if (!localStorage.getItem('nationality')) {
      navigate('/select-nationality');
    } else if (localStorage.getItem('demographic_completed') !== 'true') {
      navigate('/demographics');
    } else if (localStorage.getItem('survey_completed') !== 'true') {
      navigate('/survey');
    } else {
      navigate('/quiz');
    }
  };

  useEffect(() => {
    if (!userId) return;
    fetch(`${API_BASE}/pricing/${userId}`)
      .then(res => res.json())
      .then(data => {
        setFreeStats({
          granted: (data.free_attempts ?? 0) + (data.plays ?? 0),
          consumed: data.plays ?? 0,
        });
      })
      .catch(() => {});
  }, [userId]);

  return (
    <AppShell>
      <motion.section
        className="py-12 flex flex-col items-center text-center space-y-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-4xl sm:text-5xl font-extrabold mb-6 drop-shadow-md">
          {t('landing.title')}
        </h1>
        <p className="max-w-md text-gray-600 dark:text-gray-400 mb-6">
          Take our quick IQ test and see how you compare.
        </p>
        {freeStats && (
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Free attempts: {freeStats.granted} - {freeStats.consumed}
          </p>
        )}
        
        <button
          onClick={handleStart}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-400 via-fuchsia-500 to-purple-600 text-gray-900 dark:text-gray-100 font-semibold py-3 px-6 rounded-full shadow-md drop-shadow-glow hover:from-cyan-300 hover:to-purple-500 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-400"
        >
          {t('landing.startButton')}
          <ArrowRight className="w-5 h-5" />
        </button>
      </motion.section>
    </AppShell>
  );
}
