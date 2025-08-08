import React from 'react';
import AppShell from '../components/AppShell.jsx';
import { Outlet, Navigate } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

export default function AdminLayout() {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (!user.is_admin) {
    return <div className="p-4 text-center">Admin access required</div>;
  }
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}
