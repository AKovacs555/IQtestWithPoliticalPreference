import React from 'react';
import { Link } from 'react-router-dom';
import LanguageSelector from '../LanguageSelector';
import { useSession } from '../../hooks/useSession';
import { useTranslation } from 'react-i18next';

export default function Header() {
  const { userId, isAdmin } = useSession();
  const { t } = useTranslation();
  const pillCls =
    'h-8 px-3 rounded-full border border-[rgba(148,163,184,.25)] text-sm hover:bg-[rgba(6,182,212,.08)]';
  return (
    <header data-b-spec="header-no-tabs" className="no-tabs-header">
      <div className="mx-auto max-w-6xl flex items-center justify-between gap-2 px-4 md:px-6 h-14 md:h-16">
        <Link
          to="/"
          aria-label="Home"
          className="shrink text-[22px] sm:text-[26px] font-extrabold tracking-tight gradient-text-gold leading-none"
        >
          IQ Arena
        </Link>
        <div className="flex items-center gap-2 ml-auto" data-b-spec="controls-v2">
          <LanguageSelector className={pillCls} />
          {isAdmin && (
            <Link to="/admin" className={pillCls}>
              {t('nav.admin', { defaultValue: 'Admin' })}
            </Link>
          )}
          {userId ? (
            <Link to="/profile" className={pillCls}>
              {t('nav.profile', { defaultValue: 'Profile' })}
            </Link>
          ) : (
            <Link to="/login" className={pillCls}>
              {t('nav.login', { defaultValue: 'Log in' })}
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
