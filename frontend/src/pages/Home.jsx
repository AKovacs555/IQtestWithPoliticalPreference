import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '../auth/useAuth';

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function Home() {
  const { t } = useTranslation();
  const userId = localStorage.getItem('user_id') || '';
  const { user } = useAuth();
  const navigate = useNavigate();
  const [proPrice, setProPrice] = useState(0);
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
      .then(res => {
        if (!res.ok) throw new Error('pricing');
        return res.json();
      })
      .then(data => {
        setProPrice(data?.pro_pass?.amount_minor ?? 0);
      })
      .catch(() => {
        setProPrice(0);
      });
  }, [userId]);

  const handleProPurchase = () => {
    fetch(`${API_BASE}/purchase`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, amount: proPrice, pay_currency: 'usdttrc20' })
    })
      .then(res => res.json())
      .then(data => { if (data.payment_url) window.location = data.payment_url; });
  };

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
        {proPrice > 0 && (
          <div className="w-full grid gap-4 md:grid-cols-2">
            <div className="p-4 border rounded-md text-center">
              <h3 className="font-semibold mb-2">Pro Pass</h3>
              <p className="text-3xl font-bold">{proPrice}</p>
              <p className="text-sm text-muted-foreground">JPY / mo</p>
              <button
                onClick={handleProPurchase}
                className="mt-2 px-4 py-2 rounded-md bg-primary text-white"
              >
                Purchase
              </button>
            </div>
          </div>
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
