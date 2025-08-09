import { useAuth } from "../auth/useAuth";

/** Derive isAdmin from JWT claims or user metadata. */
export function useIsAdmin(): boolean {
  const { user } = useAuth();
  const claim = (user as any)?.is_admin;
  const meta = (user as any)?.user_metadata?.is_admin;
  const appMeta = (user as any)?.app_metadata?.is_admin;
  return Boolean(claim ?? meta ?? appMeta);
}
