import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function AdminHome() {
  const { t } = useTranslation();
  const sections = [
    { to: '/admin/questions', label: 'Questions' },
    { to: '/admin/stats', label: 'Question Stats' },
    { to: '/admin/sets', label: t('admin_sets.title') },
    { to: '/admin/settings', label: t('settings', { defaultValue: 'Settings' }) },
  ];
  return (
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
  );
}
