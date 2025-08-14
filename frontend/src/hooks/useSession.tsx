import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabaseClient';
import { waitForSession } from '../lib/waitForSession';

interface SessionContextValue {
  session: Session | null;
  user: User | null;
  userId: string | null;
  isAdmin: boolean;
  loading: boolean;
  refresh: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue>({
  session: null,
  user: null,
  userId: null,
  isAdmin: false,
  loading: true,
  refresh: async () => {},
});

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  async function fetchAndApplyIsAdmin(
    uid?: string | null,
    attempt = 0,
  ): Promise<boolean> {
    if (!uid) {
      setIsAdmin(false);
      return false;
    }
    try {
      const { data, error } = await supabase
        .from('app_users')
        .select('is_admin')
        .eq('id', uid)
        .single();
      if (!error && data) {
        const admin = Boolean(data.is_admin);
        setIsAdmin(admin);
        return admin;
      }
      if (
        (error?.code === 'PGRST116' || error?.code === 'PGRST204' || error?.code === '406') &&
        attempt < 3
      ) {
        // 404/406/キャッシュ未反映 → 300ms 後に再試行
        await new Promise((r) => setTimeout(r, 300));
        return fetchAndApplyIsAdmin(uid, attempt + 1);
      }
    } catch {}
    setIsAdmin(false);
    return false;
  }

  const applySession = async (sess: Session | null) => {
    setSession(sess);
    const uid = sess?.user?.id ?? null;
    setUserId(uid);
    if (!uid) {
      setIsAdmin(false);
    } else {
      const adminFromToken = Boolean(
        sess?.user?.user_metadata?.is_admin ||
          sess?.user?.app_metadata?.is_admin,
      );
      setIsAdmin((prev) => adminFromToken || prev);
    }
    try {
      if (sess?.access_token) {
        localStorage.setItem('authToken', sess.access_token);
      } else {
        localStorage.removeItem('authToken');
      }
      if (uid) {
        localStorage.setItem('user_id', uid);
      } else {
        localStorage.removeItem('user_id');
      }
    } catch {
      /* ignore */
    }
    await fetchAndApplyIsAdmin(uid);
  };

  const refresh = async () => {
    const { data } = await supabase.auth.getSession();
    await applySession(data.session);
  };

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const sess = await waitForSession().catch(() => null);
        if (!mounted) return;
        await applySession(sess);
        fetchAndApplyIsAdmin(sess?.user?.id);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    const { data: sub } = supabase.auth.onAuthStateChange(async () => {
      if (!mounted) return;
      const { data } = await supabase.auth.getSession();
      applySession(data.session);
      fetchAndApplyIsAdmin(data.session?.user?.id);
    });
    return () => {
      mounted = false;
      sub.subscription.unsubscribe();
    };
  }, []);

  return (
    <SessionContext.Provider
      value={{
        session,
        user: session?.user ?? null,
        userId,
        isAdmin,
        loading,
        refresh,
      }}
    >
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  return useContext(SessionContext);
}

if (typeof window !== 'undefined') {
  window.addEventListener('error', (e) =>
    console.error('GlobalError', (e as ErrorEvent).error ?? e)
  );
  window.addEventListener('unhandledrejection', (e) =>
    console.error('UnhandledRejection', (e as PromiseRejectionEvent).reason)
  );
}
