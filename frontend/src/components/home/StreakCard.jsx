import React from 'react';
import { Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export default function StreakCard({ days }) {
  const { t } = useTranslation();
  return (
    <div
      data-b-spec="card-streak"
      className="gold-card p-5 min-h-20 text-center space-y-2"
    >
      <div className="flex items-center justify-center gap-2">
        <Zap className="w-5 h-5 text-amber-300" />
        <span className="font-semibold text-white">
          {t('home.streak', { defaultValue: '連続達成' })}
        </span>
      </div>
      <div className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
        {days}
        {t('home.days', { defaultValue: '日' })}
      </div>
      <p className="text-sm text-[var(--text-muted)]">
        {t('home.streak_sub', { defaultValue: 'ストリーク日数' })}
      </p>
    </div>
  );
}
