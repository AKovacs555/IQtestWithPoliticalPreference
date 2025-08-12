import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSession } from '../hooks/useSession';

export default function RequireAdmin({
  children,
}: {
  children: JSX.Element;
}) {
  const { session, loading } = useSession();
  if (loading) return null;
  const isAdmin = Boolean(session?.user?.app_metadata?.is_admin);
  return isAdmin ? children : <Navigate to="/" replace />;
}

