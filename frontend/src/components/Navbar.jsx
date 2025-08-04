import React from 'react';
import { Link } from 'react-router-dom';
import { Disclosure } from '@headlessui/react';
import { Menu, X } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import PointsBadge from './PointsBadge';
import LanguageSelector from './LanguageSelector';
import { useTranslation } from 'react-i18next';

export default function Navbar() {
  const userId =
    typeof window !== 'undefined' ? localStorage.getItem('user_id') : null;
  const showAdmin = import.meta.env.VITE_SHOW_ADMIN === 'true' || import.meta.env.DEV;
  const { t } = useTranslation();

  const links = [
    { to: '/leaderboard', label: t('nav.leaderboard') },
    { to: '/pricing', label: t('nav.pricing') },
    { to: '/select-nationality', label: t('nav.nationality') },
    { to: '/dashboard', label: t('dashboard.title') },
    { to: '/test', label: t('nav.take_quiz'), primary: true },
  ];

  const adminLinks = [
    { to: '/admin/upload', label: 'Upload' },
    { to: '/admin/questions', label: 'Questions' },
  ];

  return (
    <Disclosure as="nav" className="backdrop-blur-md bg-white/50 dark:bg-slate-800/60 border-b border-white/20 dark:border-slate-700/60 shadow-sm">
      {({ open }) => (
        <>
          <div className="mx-auto max-w-screen-sm px-4 sm:px-8">
            <div className="flex h-14 items-center justify-between">
              <Link to="/" className="text-lg font-bold text-gray-900 dark:text-slate-100">IQ Test</Link>
              <div className="hidden md:flex md:items-center md:space-x-4">
                <ThemeToggle />
                <LanguageSelector />
                <PointsBadge userId={userId} />
                {links.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={
                      link.primary
                        ? 'px-4 py-2 rounded-md bg-primary text-white hover:bg-primary/90 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary'
                        : 'px-4 py-2 rounded-md hover:bg-gray-200 dark:hover:bg-slate-700 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary'
                    }
                  >
                    {link.label}
                  </Link>
                ))}
                {showAdmin && (
                  adminLinks.map((link) => (
                    <Link key={link.to} to={link.to} className="px-4 py-2 rounded-md hover:bg-gray-200 dark:hover:bg-slate-700 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary">
                      {link.label}
                    </Link>
                  ))
                )}
              </div>
              <div className="md:hidden flex items-center">
                <Disclosure.Button className="inline-flex items-center justify-center rounded-md p-2 hover:bg-gray-200 dark:hover:bg-slate-700 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary">
                  <span className="sr-only">Open main menu</span>
                  {open ? (
                    <X className="h-6 w-6" aria-hidden="true" />
                  ) : (
                    <Menu className="h-6 w-6" aria-hidden="true" />
                  )}
                </Disclosure.Button>
              </div>
            </div>
          </div>

          <Disclosure.Panel className="md:hidden px-4 pb-4 space-y-2">
            <ThemeToggle />
            <LanguageSelector />
            <PointsBadge userId={userId} />
            {links.map((link) => (
              <Link key={link.to} to={link.to} className="block px-4 py-2 rounded-md hover:bg-gray-200 dark:hover:bg-slate-700 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary">
                {link.label}
              </Link>
            ))}
            {showAdmin && (
              adminLinks.map((link) => (
                <Link key={link.to} to={link.to} className="block px-4 py-2 rounded-md hover:bg-gray-200 dark:hover:bg-slate-700 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary">
                  {link.label}
                </Link>
              ))
            )}
          </Disclosure.Panel>
        </>
      )}
    </Disclosure>
  );
}
