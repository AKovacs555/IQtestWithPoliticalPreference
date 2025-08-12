import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import Spinner from './common/Spinner';
import { useSession } from '../hooks/useSession';
import { useIsAdmin } from '../lib/admin';

export default function RequireAdmin({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useSession();
  const isAdmin = useIsAdmin();
  const loc = useLocation();
  if (loading) return <Spinner />;
  if (!user || !isAdmin) return <Navigate to="/" replace state={{ from: loc }} />;
  return <>{children}</>;
}
