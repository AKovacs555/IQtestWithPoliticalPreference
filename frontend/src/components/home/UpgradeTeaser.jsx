import React from 'react';
import { Link } from 'react-router-dom';
import { useSession } from '../../hooks/useSession';
import { useTranslation } from 'react-i18next';

export default function UpgradeTeaser({ to = '/upgrade' }) {
  const { user } = useSession();
  const { t } = useTranslation();
  const isPro =
    user?.pro_active_until && new Date(user.pro_active_until) > new Date();
  if (isPro) return null;
  return (
    <section
      data-b-spec="banner-pro"
      className="banner-wrap gold-ring gold-sheen bg-pro-gradient text-white sm:flex sm:items-center sm:justify-between"
      role="region"
      aria-label="Pro会員になろう"
    >
      <div className="text-center sm:text-left">
        <h3 className="text-xl sm:text-2xl font-semibold">Pro会員になろう</h3>
        <p className="text-sm opacity-90">無制限テスト・広告なし</p>
      </div>
      <Link
        to={to}
        className="inline-flex items-center justify-center h-11 px-5 rounded-xl bg-amber-500 hover:shadow-lg hover:shadow-amber-500/50 font-bold mt-4 sm:mt-0"
      >
        {t('upgrade.upgrade_now', { defaultValue: 'アップグレード' })}
      </Link>
    </section>
  );
}

