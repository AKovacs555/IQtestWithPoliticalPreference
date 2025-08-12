import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import Spinner from "./common/Spinner";
import { useSession } from "../hooks/useSession";
import { useIsAdmin } from "../lib/admin";
import { useAuth } from "../auth/useAuth";

export default function RequireAdmin({
  children,
}: {
  children: React.ReactNode;
}) {
  const { session, loaded } = useSession();
  const auth = useAuth();
  const isAdmin = useIsAdmin();
  const loc = useLocation();
  const ready = loaded || auth.loaded;
  const user = session?.user || auth.user;
  if (!ready) return <Spinner />;
  if (!user || !isAdmin) return <Navigate to="/" replace state={{ from: loc }} />;
  return <>{children}</>;
}
