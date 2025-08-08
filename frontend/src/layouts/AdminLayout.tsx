import React from 'react';
import AppShell from '../components/AppShell.jsx';
import { NavLink, Outlet, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useAuth from '../hooks/useAuth';

export default function AdminLayout() {
  const { user } = useAuth();
  const { t } = useTranslation();
  const showAdmin = String(import.meta.env.VITE_SHOW_ADMIN || '').toLowerCase() === 'true';

  if (!showAdmin) {
    return <div className="p-4 text-center">Admin UI disabled</div>;
  }
  if (!user) {
    return (
      <>
        <div className="p-4 text-center">Redirecting to login...</div>
        <Navigate to="/login" replace />
      </>
    );
  }
  if (!user.is_admin) {
    return <div className="p-4 text-center">Admin access required</div>;
  }

  const items = [
    { to: '/admin/questions', label: 'Questions' },
    { to: '/admin/stats', label: 'Question Stats' },
    { to: '/admin/sets', label: t('admin_sets.title') },
    { to: '/admin/settings', label: t('settings', { defaultValue: 'Settings' }) },
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
