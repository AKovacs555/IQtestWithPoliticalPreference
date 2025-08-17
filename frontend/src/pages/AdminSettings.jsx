import React from 'react';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';

export default function AdminSettings() {
  return (
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <h2 className="text-xl font-semibold mb-4">Admin Settings</h2>
          <p>Settings placeholder</p>
        </div>
      </AdminScaffold>
    </>
  );
}
