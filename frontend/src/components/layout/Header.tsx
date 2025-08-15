import React from 'react';
import { Link } from 'react-router-dom';
import Navbar, { getNavLinks } from '../Navbar';
import LanguageSelector from '../LanguageSelector';
import PointsBadge from '../PointsBadge';
import { useSession } from '../../hooks/useSession';
import { useTranslation } from 'react-i18next';
import MobileDrawer from '../nav/MobileDrawer';

export default function Header() {
  const { userId, isAdmin } = useSession();
  const { t } = useTranslation();
  const drawerItems = getNavLinks(t, isAdmin).map((l) => ({
    label: l.label,
    href: l.to,
  }));
  const pillCls =
    'flex items-center h-8 px-3 rounded-full border border-[rgba(148,163,184,.25)] text-sm hover:bg-[rgba(6,182,212,.08)]';

  return (
    <header
      data-b-spec="header-v2"
      className="sticky top-0 z-50 backdrop-blur-md bg-[var(--glass)] border-b border-[var(--border)]"
    >
      <div className="relative flex items-center justify-center px-4 md:px-6 h-14 md:h-16">
        <div className="absolute left-4 md:left-6 flex items-center md:hidden">
          <MobileDrawer items={drawerItems} buttonClassName="text-[var(--text)]" />
        </div>
        <Link to="/" aria-label="Home">
          <span className="gradient-text-gold text-[28px] leading-tight font-extrabold tracking-tight">
            IQ Arena
          </span>
        </Link>
        <div
          className="absolute right-4 md:right-6 flex items-center gap-2"
          data-b-spec="controls-v1"
        >
          <div className={pillCls}>Bronze</div>
          <PointsBadge userId={userId} className={pillCls} />
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
      <Navbar />
    </header>
  );
}
