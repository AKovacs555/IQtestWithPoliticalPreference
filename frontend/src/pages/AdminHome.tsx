import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';

export default function AdminHome() {
  const { t } = useTranslation();
  const sections = [
    { to: '/admin/questions', label: 'Questions' },
    { to: '/admin/stats', label: 'Question Stats' },
    { to: '/admin/sets', label: t('admin_sets.title') },
    { to: '/admin/settings', label: t('settings', { defaultValue: 'Settings' }) },
    { to: '/admin/surveys', label: 'Surveys' },       // **Restored Surveys management section**
    { to: '/admin/users', label: 'Users' },
    { to: '/admin/pricing', label: 'Pricing' },
    { to: '/admin/referral', label: 'Referral' }
  ];
  return (
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <div className="grid gap-4 sm:grid-cols-2">
            {sections.map((s) => (
              <Link
                key={s.to}
                to={s.to}
                className="block p-4 border rounded hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                {s.label}
              </Link>
            ))}
          </div>
        </div>
      </AdminScaffold>
    </>
  );
}
