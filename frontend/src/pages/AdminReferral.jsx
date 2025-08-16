import React from 'react';
import AdminHeroTop from '../components/admin/AdminHeroTop';
import AdminScaffold from '../components/admin/AdminScaffold';

export default function AdminReferral() {
  return (
    <>
      <AdminHeroTop />
      <AdminScaffold>
        <div className="gold-ring glass-surface p-4" data-b-spec="admin-card-theme">
          <h2 className="mb-4 text-xl font-semibold">Referral</h2>
          <p>Manage referral limits and view referral stats.</p>
        </div>
      </AdminScaffold>
    </>
  );
}
