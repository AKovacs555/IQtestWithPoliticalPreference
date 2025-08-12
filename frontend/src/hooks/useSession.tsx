import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabaseClient';

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

  const applySession = (sess: Session | null) => {
    setSession(sess);
    const uid = sess?.user?.id ?? null;
    setUserId(uid);
    setIsAdmin(Boolean(sess?.user?.app_metadata?.is_admin));
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
  };

  const refresh = async () => {
    const { data } = await supabase.auth.getSession();
    applySession(data.session);
  };

  useEffect(() => {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, sess) => {
      applySession(sess);
      if (event === 'INITIAL_SESSION') setLoading(false);
    });
    supabase.auth
      .getSession()
      .then(({ data }) => applySession(data.session))
      .finally(() => setLoading(false));
    return () => {
      subscription.unsubscribe();
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
