import React from 'react';
import { Trophy } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import ShareButton from '../share/ShareButton';

export default function CurrentIQCard({ score, inviteCode }) {
  const { t } = useTranslation();
  return (
    <div
      data-b-spec="card-iq"
      className="gold-card relative p-5 min-h-20 text-center space-y-2"
    >
      <div className="flex items-center justify-center gap-2">
        <Trophy className="w-5 h-5 text-amber-300" />
        <span className="font-semibold text-white">
          {t('home.current_iq', { defaultValue: '現在のIQ' })}
        </span>
      </div>
      <div className="text-4xl md:text-5xl font-extrabold text-white">{Number(score ?? 0).toFixed(2)}</div>
      <p className="text-sm text-[var(--text-muted)]">
        {t('home.current_iq_sub', { defaultValue: '最新のIQスコア' })}
      </p>
      {inviteCode && (
        <div className="absolute bottom-2 left-2">
          <ShareButton
            size="small"
            label={t('share.button')}
            url={`${location.origin}?code=${inviteCode}`}
            title={t('home.share_title', { defaultValue: '結果を共有' })}
            text={t('home.share_text', { defaultValue: `私のIQは${Number(score ?? 0).toFixed(2)}でした。` })}
          />
        </div>
      )}
    </div>
  );
}
