import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { SHOW_ADMIN, useIsAdmin } from "../lib/admin";

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const isAdmin = useIsAdmin();
  const loc = useLocation();
  if (!SHOW_ADMIN) return <Navigate to="/" replace state={{ from: loc }} />;
  return isAdmin ? <>{children}</> : <Navigate to="/" replace state={{ from: loc }} />;
}
