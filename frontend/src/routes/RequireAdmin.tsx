import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSession } from '../hooks/useSession';

export default function RequireAdmin({ children }: { children: ReactNode }) {
  const { isAdmin, loading } = useSession();
  const loc = useLocation();
  if (loading) return null;
  if (!isAdmin) return <Navigate to="/" replace state={{ from: loc }} />;
  return <>{children}</>;
}
