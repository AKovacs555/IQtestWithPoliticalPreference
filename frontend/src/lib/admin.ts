import { useAuth } from '../auth/useAuth';

export function useIsAdmin() {
  const { user } = useAuth();
  const u: any = user;
  return Boolean(u?.is_admin ?? u?.user_metadata?.is_admin ?? u?.app_metadata?.is_admin);
}
