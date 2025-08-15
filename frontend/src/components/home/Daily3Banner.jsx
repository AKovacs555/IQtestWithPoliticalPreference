import React from 'react';
import { useTranslation } from 'react-i18next';

export default function Daily3Banner({
  progress = 0,
  onNext,
  onWatchAd,
  resetText = '',
}) {
  const { t } = useTranslation();
  const pct = Math.max(0, Math.min(100, progress));
  return (
    <section
      data-b-spec="banner-daily3"
      className="banner-wrap gold-ring gold-sheen card-glass text-[var(--text)]"
      role="region"
      aria-label="Daily 3"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex h-6 w-6 rounded-full bg-emerald-500/20 items-center justify-center">🧠</span>
          <h2 className="text-xl font-semibold">Daily 3</h2>
        </div>
        {resetText && (
          <div className="text-sm text-[var(--text-muted)]">{resetText}</div>
        )}
      </div>
      <div className="progress-track">
        <div className="progress-bar" style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-4 flex flex-col sm:flex-row gap-3">
        <button type="button" onClick={onNext} className="btn-primary w-full sm:w-auto">
          {t('home.next_question', { defaultValue: '次の質問に答える' })}
        </button>
        <button type="button" onClick={onWatchAd} className="btn-outline w-full sm:w-auto">
          {t('home.watch_ad_plus', { defaultValue: '広告を見て +1回' })}
        </button>
      </div>
    </section>
  );
}

