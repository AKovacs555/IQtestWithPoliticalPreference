import { useEffect, useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabaseClient';
import { fetchProfile, fetchWithAuth } from '../lib/api';

export function useAuth() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function loadProfile(session: Session) {
    localStorage.setItem('authToken', session.access_token);
    if (session.user?.id) localStorage.setItem('user_id', session.user.id);
    try {
      let profile;
      try {
        profile = await fetchProfile();
      } catch (err: any) {
        if (String(err.message) === '401') {
          await fetchWithAuth('/user/ensure', { method: 'POST', body: JSON.stringify({}) });
          profile = await fetchProfile();
        } else {
          throw err;
        }
      }
      setUser({
        ...(session.user as any),
        is_admin: profile.is_admin,
        app_metadata: { ...(session.user?.app_metadata || {}), is_admin: profile.is_admin },
      });
    } catch {
      setUser(session.user as any);
    }
  }

  useEffect(() => {
    (async () => {
      try {
        const { data } = await supabase.auth.getSession();
        const session = data.session;
        if (session?.access_token) {
          await loadProfile(session);
        }
      } finally {
        setLoading(false);
      }
    })();

    const { data: sub } = supabase.auth.onAuthStateChange(async (ev, session) => {
      if (ev === 'SIGNED_IN' && session) {
        await loadProfile(session);
      }
      if (ev === 'SIGNED_OUT') {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user_id');
        setUser(null);
      }
    });
    return () => {
      sub.subscription?.unsubscribe();
    };
  }, []);

  return { user, loading };
}
