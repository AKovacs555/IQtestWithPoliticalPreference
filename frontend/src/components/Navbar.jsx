import React from 'react';
import { Link } from 'react-router-dom';
import { Disclosure } from '@headlessui/react';
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline';
import ThemeToggle from './ThemeToggle';
import PointsBadge from './PointsBadge';
import LanguageSelector from './LanguageSelector';
import { useTranslation } from 'react-i18next';

export default function Navbar() {
  const userId = 'demo';
  const showAdmin = import.meta.env.VITE_SHOW_ADMIN === 'true' || import.meta.env.DEV;
  const { t } = useTranslation();

  const links = [
    { to: '/leaderboard', label: 'Leaderboard' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/select-nationality', label: 'Nationality' },
    { to: '/select-party', label: 'Parties' },
    { to: '/dashboard', label: t('dashboard.title') },
    { to: '/test', label: 'Take Quiz', primary: true },
  ];

  const adminLinks = [
    { to: '/admin/upload', label: 'Upload' },
    { to: '/admin/questions', label: 'Questions' },
  ];

  return (
    <Disclosure as="nav" className="bg-surface shadow-sm">
      {({ open }) => (
        <>
          <div className="mx-auto max-w-screen-lg px-4">
            <div className="flex h-14 items-center justify-between">
              <Link to="/" className="text-lg font-bold">IQ Test</Link>
              <div className="hidden md:flex md:items-center md:space-x-4">
                <ThemeToggle />
                <LanguageSelector />
                <PointsBadge userId={userId} />
                {links.map((link) => (
                  <Link
                    key={link.to}
                    to={link.to}
                    className={link.primary ? 'px-3 py-2 rounded-md bg-primary text-white' : 'px-3 py-2 rounded-md hover:bg-gray-200'}
                  >
                    {link.label}
                  </Link>
                ))}
                {showAdmin && (
                  adminLinks.map((link) => (
                    <Link key={link.to} to={link.to} className="px-3 py-2 rounded-md hover:bg-gray-200">
                      {link.label}
                    </Link>
                  ))
                )}
              </div>
              <div className="md:hidden flex items-center">
                <Disclosure.Button className="inline-flex items-center justify-center rounded-md p-2 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-primary">
                  <span className="sr-only">Open main menu</span>
                  {open ? (
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  ) : (
                    <Bars3Icon className="h-6 w-6" aria-hidden="true" />
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
              <Link key={link.to} to={link.to} className="block px-3 py-2 rounded-md hover:bg-gray-200">
                {link.label}
              </Link>
            ))}
            {showAdmin && (
              adminLinks.map((link) => (
                <Link key={link.to} to={link.to} className="block px-3 py-2 rounded-md hover:bg-gray-200">
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
