import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
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
  logout: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue>({
  session: null,
  user: null,
  userId: null,
  isAdmin: false,
  loading: true,
  refresh: async () => {},
  logout: async () => {},
});

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

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
    await fetchAndApplyIsAdmin(uid);
  };

  const refresh = async () => {
    const { data } = await supabase.auth.getSession();
    await applySession(data.session);
  };

  const logout = async () => {
    await supabase.auth.signOut();
  };

  useEffect(() => {
    let mounted = true;
    (async () => {
      const { data } = await supabase.auth.getSession();
      let sess = data.session;
      const hasCode = /[?&]code=/.test(window.location.href);
      if (!sess && hasCode) {
        sess = await waitForSession().catch(() => null);
      }
      if (!mounted) return;
      await applySession(sess);
      fetchAndApplyIsAdmin(sess?.user?.id);
      setLoading(false);
    })();
    const { data: sub } = supabase.auth.onAuthStateChange((event, sess) => {
      if (!mounted) return;
      applySession(sess);
      fetchAndApplyIsAdmin(sess?.user?.id);
      if (event === 'SIGNED_IN') navigate('/');
      if (event === 'SIGNED_OUT') navigate('/login');
    });
    return () => {
      mounted = false;
      sub.subscription.unsubscribe();
    };
  }, [navigate]);

  return (
    <SessionContext.Provider
      value={{
        session,
        user: session?.user ?? null,
        userId,
        isAdmin,
        loading,
        refresh,
        logout,
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
