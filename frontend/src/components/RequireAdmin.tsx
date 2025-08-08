import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useIsAdmin } from "../lib/admin";

export default function RequireAdmin({
  children,
}: {
  children: React.ReactNode;
}) {
  const isAdmin = useIsAdmin();
  const loc = useLocation();
  if (!isAdmin) return <Navigate to="/" replace state={{ from: loc }} />;
  return <>{children}</>;
}
