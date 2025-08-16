import React from 'react';
import AppShell from '../components/AppShell';
import { NavLink, Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function AdminLayout() {
  const { t } = useTranslation();

  const items = [
    { to: '/admin/questions', label: 'Questions' },
    { to: '/admin/stats', label: 'Question Stats' },
    { to: '/admin/surveys', label: 'Surveys' },
    { to: '/admin/sets', label: t('admin_sets.title') },
    { to: '/admin/settings', label: t('settings', { defaultValue: 'Settings' }) },
    { to: '/admin/pricing', label: 'Pricing' },
    { to: '/admin/referral', label: 'Referral' },
  ];

  return (
    <AppShell>
      <div className="grid grid-cols-1 md:grid-cols-[220px_1fr] gap-4">
        <nav className="md:sticky md:top-16">
          <ul className="flex md:block overflow-x-auto md:overflow-visible">
            {items.map(item => (
              <li key={item.to} className="mr-4 md:mr-0">
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `block px-3 py-2 rounded-md ${
                      isActive
                        ? 'font-semibold underline'
                        : 'opacity-80 hover:opacity-100'
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main className="min-h-[60vh]">
          <Outlet />
        </main>
      </div>
    </AppShell>
  );
}
