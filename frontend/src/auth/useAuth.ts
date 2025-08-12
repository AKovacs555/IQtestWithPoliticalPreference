import { useSession } from '../hooks/useSession';

export function useAuth() {
  const { user, userId, isAdmin, loading } = useSession();
  const userWithFlag = user ? { ...user, is_admin: isAdmin } : null;
  return { user: userWithFlag, userId, isAdmin, loaded: !loading, loading };
}

