import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import Spinner from "./common/Spinner";

export default function RequireAdmin({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loaded } = useAuth();
  const loc = useLocation();
  if (!loaded) return <Spinner />;
  if (!user?.is_admin) return <Navigate to="/" replace state={{ from: loc }} />;
  return <>{children}</>;
}
