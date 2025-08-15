import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation, type TFunction } from 'react-i18next';
import { useSession } from '../hooks/useSession';

export interface NavLinkItem {
  to: string;
  label: string;
}

export function getNavLinks(t: TFunction, isAdmin: boolean): NavLinkItem[] {
  const links: NavLinkItem[] = [
    { to: '/', label: t('nav.home', { defaultValue: 'Home' }) },
    { to: '/test', label: t('nav.take_quiz') },
    { to: '/leaderboard', label: t('nav.leaderboard') },
    { to: '/pricing', label: t('nav.pricing') },
  ];

  if (isAdmin) {
    links.push({ to: '/admin', label: t('nav.admin', { defaultValue: 'Admin' }) });
  }

  return links;
}

export default function Navbar() {
  const { t } = useTranslation();
  const { isAdmin } = useSession();
  const links = getNavLinks(t, isAdmin);

  return (
    <nav className="hidden md:flex justify-center gap-6 px-4 md:px-6 py-2 text-sm">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          className={({ isActive }) =>
            `transition-colors hover:text-white ${isActive ? 'text-white' : 'text-[var(--text-muted)]'}`
          }
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
