import React from 'react';
import { useTranslation } from 'react-i18next';

export default function TestStartBanner({
  freeLabel = '無料テストが利用可能です！',
  statLeft = { label: '無料受験回数', sub: 'Daily 3完了で獲得', icon: '⚡' },
  statRight = { value: '2', label: '回利用可能' },
  onStart,
}) {
  const { t } = useTranslation();
  return (
    <section
      data-b-spec="banner-teststart"
      className="banner-wrap gold-ring gold-sheen card-glass text-[var(--text)]"
      role="region"
      aria-label="IQテスト受験"
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="inline-flex h-6 w-6 rounded-full bg-cyan-500/20 items-center justify-center">🧠</span>
        <h2 className="text-xl font-semibold">IQテスト受験</h2>
      </div>
      <p className="text-sm text-[var(--text-muted)] mb-4">{freeLabel}</p>
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="col-span-2 rounded-lg border border-[rgba(148,163,184,.25)] bg-emerald-700/10 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-8 w-8 rounded-full bg-emerald-500/25 items-center justify-center">{statLeft.icon}</span>
            <div>
              <div className="font-medium">{statLeft.label}</div>
              <div className="text-xs text-[var(--text-muted)]">{statLeft.sub}</div>
            </div>
          </div>
        </div>
        <div className="rounded-lg border border-[rgba(148,163,184,.25)] bg-emerald-700/10 px-4 py-3 text-right">
          <div className="text-2xl font-bold">{statRight.value}</div>
          <div className="text-xs text-[var(--text-muted)]">{statRight.label}</div>
        </div>
      </div>
      <button type="button" onClick={onStart} className="w-full h-12 rounded-lg text-white font-semibold bg-cta-gradient hover:shadow-lg">
        {t('home.start_iq', { defaultValue: 'IQテストを開始する' })}
      </button>
    </section>
  );
}

