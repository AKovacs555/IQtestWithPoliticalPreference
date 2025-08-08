import useAuth from "../hooks/useAuth";

export const SHOW_ADMIN: boolean =
  (import.meta.env.VITE_SHOW_ADMIN ?? "false") === "true";

/** Derive isAdmin from JWT claims or user metadata, with a server fallback if already present in state. */
export function useIsAdmin(): boolean {
  const { user } = useAuth();
  const claim = (user as any)?.is_admin;
  const meta = (user as any)?.user_metadata?.is_admin;
  return Boolean(claim ?? meta);
}
