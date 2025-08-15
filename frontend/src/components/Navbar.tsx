import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useSession } from '../hooks/useSession';

export default function Navbar() {
  const { t } = useTranslation();
  const { isAdmin } = useSession();

  const links = [
    { to: '/', label: t('nav.home', { defaultValue: 'Home' }) },
    { to: '/test', label: t('nav.take_quiz') },
    { to: '/leaderboard', label: t('nav.leaderboard') },
    { to: '/pricing', label: t('nav.pricing') },
  ];

  if (isAdmin) {
    links.push({ to: '/admin', label: t('nav.admin', { defaultValue: 'Admin' }) });
  }

  return (
    <nav className="hidden md:flex items-center gap-4">
      {links.map((link) => (
        <NavLink
          key={link.to}
          to={link.to}
          className={({ isActive }) =>
            `text-sm whitespace-nowrap transition-colors hover:text-white ${
              isActive ? 'text-white' : 'text-[var(--text-muted)]'
            }`
          }
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}

