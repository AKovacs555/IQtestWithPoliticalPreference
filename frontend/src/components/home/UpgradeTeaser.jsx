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
      data-b-spec="pricing-banner-pro-v2"
      className="rounded-xl gold-card bg-gradient-pro shadow-gold px-6 py-8 sm:flex sm:items-center sm:justify-between text-white"
    >
      <div className="text-center sm:text-left">
        <h3 className="text-xl sm:text-2xl font-semibold">
          {t('upgradeBanner.title', { defaultValue: 'Pro会員になろう' })}
        </h3>
        <p className="text-sm">
          {t('upgradeBanner.subtitle', { defaultValue: '無制限テスト・広告なし' })}
        </p>
      </div>
      <div className="mt-4 sm:mt-0 text-center sm:text-right">
        <Link
          to="/upgrade"
          className="inline-block h-11 px-5 rounded-xl bg-amber-500 hover:shadow-lg hover:shadow-amber-500/50 text-white font-bold"
        >
          {t('upgradeBanner.upgradeNow', { defaultValue: '今すぐアップグレード' })}
        </Link>
      </div>
    </div>
  );
}
