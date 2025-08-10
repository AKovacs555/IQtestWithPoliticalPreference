import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabaseClient';

export function useAuth() {
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const init = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      if (session?.access_token) {
        localStorage.setItem('authToken', session.access_token);
      }
      if (session?.user?.id) {
        localStorage.setItem('user_id', session.user.id);
      }
    };
    init();

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
      if (session?.access_token) {
        localStorage.setItem('authToken', session.access_token);
      }
      if (session?.user?.id) {
        localStorage.setItem('user_id', session.user.id);
        // Ensure we have a row in public.users
        fetch('/auth/upsert_user', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: session.user.id })
        }).catch(() => {});
      }
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  return { user, supabase };
}
