import React from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';

export default function Home() {
  const { t } = useTranslation();
  return (
    <Layout>
      <section className="text-center space-y-6 py-12">
        <h1 className="text-4xl font-bold">{t('take_quiz')}</h1>
        <p className="max-w-xl mx-auto">Take our quick adaptive test and see how you compare.</p>
        <div className="space-x-2">
          <Link to="/start" className="btn btn-primary">{t('take_quiz')}</Link>
          <Link to="/pricing" className="btn btn-secondary">Pricing</Link>
        </div>
        <div className="max-w-md mx-auto mt-8">
          <blockquote className="text-sm italic">“A fun way to challenge yourself and learn something new.”</blockquote>
          <p className="text-sm mt-2">— Happy User</p>
        </div>
      </section>
    </Layout>
  );
}
