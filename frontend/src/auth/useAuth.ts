import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabaseClient';
import { fetchProfile } from '../lib/api';

export function useAuth() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data: sess } = await supabase.auth.getSession();
        if (sess.session?.access_token) {
          localStorage.setItem('authToken', sess.session.access_token);
          if (sess.session.user?.id) {
            localStorage.setItem('user_id', sess.session.user.id);
          }
          try {
            const profile = await fetchProfile();
            setUser({
              ...(sess.session.user as any),
              is_admin: profile.is_admin,
              app_metadata: {
                ...(sess.session.user?.app_metadata || {}),
                is_admin: profile.is_admin,
              },
            });
          } catch {
            /* ignore */
          }
        } else if (localStorage.getItem('authToken')) {
          try {
            const profile = await fetchProfile();
            setUser({
              id: profile.id,
              is_admin: profile.is_admin,
              app_metadata: { is_admin: profile.is_admin },
            });
          } catch {
            /* ignore */
          }
        }
      } finally {
        setLoading(false);
      }
    })();

    const { data: sub } = supabase.auth.onAuthStateChange(async (ev, session) => {
      if (ev === 'SIGNED_IN' && session?.access_token) {
        localStorage.setItem('authToken', session.access_token);
        if (session.user?.id) {
          localStorage.setItem('user_id', session.user.id);
        }
        try {
          const profile = await fetchProfile();
          setUser({
            ...(session.user as any),
            is_admin: profile.is_admin,
            app_metadata: {
              ...(session.user?.app_metadata || {}),
              is_admin: profile.is_admin,
            },
          });
        } catch {
          /* ignore */
        }
      }
      if (ev === 'SIGNED_OUT') {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user_id');
        setUser(null);
      }
    });
    return () => sub.subscription?.unsubscribe();
  }, []);

  return { user, loading };
}
