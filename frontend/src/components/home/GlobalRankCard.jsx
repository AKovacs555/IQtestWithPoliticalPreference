import React from 'react';
import { Star } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function GlobalRankCard({ rank }) {
  const { t } = useTranslation();
  return (
    <div
      data-b-spec="card-rank"
      className="gold-card p-5 min-h-20 text-center space-y-2"
    >
      <div className="flex items-center justify-center gap-2">
        <Star className="w-5 h-5 text-amber-300" />
        <span className="font-semibold text-white">
          {t('home.global_rank', { defaultValue: '#順位' })}
        </span>
      </div>
      <div className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">#{rank}</div>
      <p className="text-sm text-[var(--text-muted)]">
        {t('home.global_rank_sub', { defaultValue: 'グローバルランキング' })}
      </p>
    </div>
  );
}
