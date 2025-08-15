import React from 'react';
import { Link } from 'react-router-dom';
import { useSession } from '../../hooks/useSession';
import { useTranslation } from 'react-i18next';

export default function UpgradeTeaser() {
  const { user } = useSession();
  const { t } = useTranslation();
  const isPro =
    user?.pro_active_until && new Date(user.pro_active_until) > new Date();
  if (isPro) return null;
  return (
    <div
      data-b-spec="pricing-banner-v1"
      className="relative rounded-xl border-2 border-[rgba(255,210,63,0.2)] px-6 py-8 text-center bg-[radial-gradient(circle_at_center,_rgba(255,224,130,0.35),_transparent_80%),_#0f172a] space-y-4"
    >
      <h3 className="text-xl sm:text-2xl font-semibold gradient-text-gold">
        {t('upgradeBanner.title', { defaultValue: 'さらにIQ Arenaを楽しもう' })}
      </h3>
      <p className="text-sm text-[var(--text-muted)]">
        {t('upgradeBanner.subtitle', {
          defaultValue:
            'Proになると受験が無制限になり、広告も最小限になります。',
        })}
      </p>
      <div className="flex flex-col sm:flex-row justify-center items-center gap-3 sm:gap-4 pt-2">
        <Link
          to="/upgrade"
          className="inline-block h-11 px-5 rounded-xl bg-amber-500 hover:shadow-lg hover:shadow-amber-500/50 text-white font-bold"
        >
          {t('upgradeBanner.upgradeNow', { defaultValue: '今すぐアップグレード' })}
        </Link>
        <Link
          to="/pricing"
          className="inline-block h-11 px-5 rounded-xl border border-[rgba(255,224,130,0.5)] text-amber-300 hover:bg-[rgba(255,224,130,0.1)] font-medium"
        >
          {t('upgradeBanner.seePlans', { defaultValue: 'プランを見る' })}
        </Link>
      </div>
    </div>
  );
}
