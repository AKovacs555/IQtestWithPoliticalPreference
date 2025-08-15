import React from 'react';
import { Trophy } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function CurrentIQCard({ score }) {
  const { t } = useTranslation();
  return (
    <div
      data-b-spec="card-iq"
      className="gold-card p-5 min-h-20 text-center space-y-2"
    >
      <div className="flex items-center justify-center gap-2">
        <Trophy className="w-5 h-5 text-amber-300" />
        <span className="font-semibold text-white">
          {t('home.current_iq', { defaultValue: '現在のIQ' })}
        </span>
      </div>
      <div className="text-4xl md:text-5xl font-extrabold text-white">{score}</div>
      <p className="text-sm text-[var(--text-muted)]">
        {t('home.current_iq_sub', { defaultValue: '最新のIQスコア' })}
      </p>
    </div>
  );
}
