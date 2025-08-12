import { useSession } from '../hooks/useSession';

export function useIsAdmin() {
  const { isAdmin } = useSession();
  return isAdmin;
}
