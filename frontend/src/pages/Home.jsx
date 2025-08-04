import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function Home() {
  const { t } = useTranslation();
  const [leaders, setLeaders] = useState([]);
  const [partyNames, setPartyNames] = useState({});
  const userId = localStorage.getItem('user_id') || '';

  useEffect(() => {
    fetch(`${API_BASE}/leaderboard`)
      .then((res) => res.json())
      .then((res) => setLeaders(res.leaderboard || []));
    fetch(`${API_BASE}/survey/start?user_id=${userId}`)
      .then((res) => res.json())
      .then((res) => {
        const map = {};
        (res.parties || []).forEach((p) => {
          map[p.id] = p.name;
        });
        setPartyNames(map);
      });
  }, [userId]);

  return (
    <Layout>
      <motion.section
        className="py-12 flex flex-col items-center text-center space-y-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-4xl sm:text-5xl font-extrabold mb-6">
          {t('landing.title')}
        </h1>
        <p className="max-w-md text-gray-600 mb-6">
          Take our quick IQ test and see how you compare.
        </p>
        <div className="w-full max-w-sm space-y-4 mb-10">
          {leaders.slice(0, 5).map((row, i) => (
            <motion.div
              key={row.party_id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-center justify-between bg-white/70 backdrop-blur-md rounded-2xl shadow-md p-4"
            >
              <span className="text-sm font-medium text-gray-600 text-left">
                {partyNames[row.party_id] || `Party ${row.party_id}`}
              </span>
              <span className="text-2xl font-bold">
                {Math.round(row.avg_iq)}
              </span>
            </motion.div>
          ))}
        </div>
        <Link
          to="/test"
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-primary text-white font-medium py-3 px-6 rounded-full shadow-md hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary"
        >
          {t('landing.startButton')}
          <ArrowRight className="w-5 h-5" />
        </Link>
      </motion.section>
    </Layout>
  );
}
