import React from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { useTranslation } from 'react-i18next';

export default function Home() {
  const { t } = useTranslation();
  return (
    <Layout>
      <section className="text-center py-20 px-4">
        <h1 className="text-5xl font-extrabold mb-6">{t('landing.title')}</h1>
        <p className="max-w-xl mx-auto mb-8">Take our quick IQ test and see how you compare.</p>
        <div className="flex justify-center gap-4">
          <Link to="/test" className="px-6 py-3 rounded-md bg-primary text-white">
            {t('landing.startButton')}
          </Link>
          <Link to="/pricing" className="px-6 py-3 rounded-md border border-primary text-primary">
            Pricing
          </Link>
        </div>
        <img
          src="/static/img/hero.svg"
          alt=""
          className="mx-auto mt-10 w-full max-w-md"
          loading="lazy"
        />
      </section>
    </Layout>
  );
}
