import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function ArenaBanner({ to = '/arena' }) {
  const { t } = useTranslation();
  return (
    <section
      data-b-spec="banner-arena"
      className="banner-wrap gold-ring gold-sheen card-glass text-[var(--text)]"
      role="region"
      aria-label="IQ Clash"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-6 w-6 rounded-full bg-indigo-500/20 items-center justify-center">🏟️</span>
          <h2 className="text-xl font-semibold">
            {t('home.arena_title', { defaultValue: 'IQ Clash' })}
          </h2>
        </div>
        <Link to={to} className="btn-primary">
          {t('home.enter_arena', { defaultValue: 'アリーナへ' })}
        </Link>
      </div>
    </section>
  );
}
