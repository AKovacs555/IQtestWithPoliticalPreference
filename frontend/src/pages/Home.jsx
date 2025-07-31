import React from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';
import { motion, useScroll, useTransform } from 'framer-motion';

export default function Home() {
  const { t } = useTranslation();
  const { scrollY } = useScroll();
  const y1 = useTransform(scrollY, [0, 300], [0, -100]);
  const y2 = useTransform(scrollY, [0, 300], [0, -50]);
  return (
    <Layout>
      <section className="relative text-center space-y-6 py-20 overflow-hidden">
        <motion.div style={{ y: y1 }} className="absolute inset-0 bg-gradient-to-b from-purple-500 via-transparent to-transparent h-64"/>
        <motion.h1 style={{ y: y2 }} className="text-5xl font-extrabold relative z-10">
          {t('landing.title')}
        </motion.h1>
        <p className="max-w-xl mx-auto relative z-10">Take our quick IQ test and see how you compare.</p>
        <div className="space-x-2 relative z-10">
          <Link to="/test" className="btn btn-primary">{t('landing.startButton')}</Link>
          <Link to="/pricing" className="btn btn-secondary">Pricing</Link>
        </div>
        <div className="max-w-md mx-auto mt-8 relative z-10">
          <blockquote className="text-sm italic">“A fun way to challenge yourself and learn something new.”</blockquote>
          <p className="text-sm mt-2">— Happy User</p>
        </div>
      </section>
    </Layout>
  );
}
