import React from 'react';
import { Link } from 'react-router-dom';
import LanguageSelector from '../LanguageSelector';
import { useSession } from '../../hooks/useSession';
import { useTranslation } from 'react-i18next';
import { User, LogIn } from 'lucide-react';

export default function Header() {
  const { userId, isAdmin } = useSession();
  const { t } = useTranslation();
  const pillCls =
    'flex items-center h-8 px-3 rounded-full border border-[rgba(148,163,184,.25)] text-sm hover:bg-[rgba(6,182,212,.08)]';

  return (
    <header
      data-b-spec="header-v2"
      className="sticky top-0 z-50 backdrop-blur-md bg-[var(--glass)] border-b border-[var(--border)]"
    >
      <div className="relative flex items-center justify-center px-4 md:px-6 h-14 md:h-16">
        <Link to="/" aria-label="Home">
          <span className="gradient-text-gold text-[28px] leading-tight font-extrabold tracking-tight">
            IQ Arena
          </span>
        </Link>
        <div
          className="absolute right-4 md:right-6 flex items-center gap-2"
          data-b-spec="controls-v1"
        >
          <LanguageSelector className={pillCls} />
          {isAdmin && (
            <Link to="/admin" className={pillCls}>
              {t('nav.admin', { defaultValue: 'Admin' })}
            </Link>
          )}
          {userId ? (
            <Link
              to="/profile"
              className={pillCls}
              aria-label={t('nav.profile', { defaultValue: 'Profile' })}
            >
              <User className="h-4 w-4" />
            </Link>
          ) : (
            <Link
              to="/login"
              className={pillCls}
              aria-label={t('nav.login', { defaultValue: 'Log in' })}
            >
              <LogIn className="h-4 w-4" />
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
