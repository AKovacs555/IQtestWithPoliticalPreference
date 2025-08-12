import { useSession } from '../hooks/useSession';

export function useIsAdmin() {
  const { user } = useSession();
  const u: any = user;
  return Boolean(u?.is_admin ?? u?.user_metadata?.is_admin ?? u?.app_metadata?.is_admin);
}
