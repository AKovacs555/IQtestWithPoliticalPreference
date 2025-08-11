import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabaseClient';
import { fetchWithAuth, fetchProfile } from '../lib/api';

export function useAuth() {
  const [user, setUser] = useState<any>(null);
  // ユーザー情報を取得中かどうかを示すフラグ
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 初回マウント時にセッションを取得
    (async () => {
      const { data } = await supabase.auth.getSession();
      const session = data?.session;
      const supaUser = session?.user ?? null;
      if (session?.access_token) {
        localStorage.setItem('authToken', session.access_token);
        if (supaUser?.id) localStorage.setItem('user_id', supaUser.id);
      }
      let mergedUser: any = supaUser ? { ...supaUser } : null;
      if (supaUser) {
        try {
          const profile = await fetchProfile();
          mergedUser.is_admin = profile.is_admin;
          mergedUser.app_metadata = {
            ...(mergedUser.app_metadata || {}),
            is_admin: profile.is_admin,
          };
        } catch (e) {
          console.warn('Failed to fetch profile', e);
        }
      } else if (localStorage.getItem('authToken')) {
        try {
          const profile = await fetchProfile();
          mergedUser = {
            ...profile,
            is_admin: profile.is_admin,
            app_metadata: { is_admin: profile.is_admin },
          } as any;
        } catch (e) {
          console.warn('Failed to fetch profile', e);
        }
      }
      setUser(mergedUser);
      setLoading(false);
    })();

    const { data: sub } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (session?.user) {
        const supaUser = session.user;
        if (session.access_token) {
          localStorage.setItem('authToken', session.access_token);
        }
        if (supaUser?.id) {
          localStorage.setItem('user_id', supaUser.id);
          if (event === 'SIGNED_IN') {
            // Ensure we have a row in public.app_users on first sign in
            const pending = localStorage.getItem('pending_username');
            const body: any = { user_id: supaUser.id };
            if (pending) body.username = pending;
            fetchWithAuth('/auth/upsert_user', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(body),
            })
              .then(() => {
                if (pending) localStorage.removeItem('pending_username');
              })
              .catch(() => {});
          }
          let merged: any = { ...supaUser };
          try {
            const profile = await fetchProfile();
            merged.is_admin = profile.is_admin;
            merged.app_metadata = {
              ...(merged.app_metadata || {}),
              is_admin: profile.is_admin,
            };
          } catch (e) {
            console.warn('Failed to fetch profile', e);
          }
          setUser(merged);
        }
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        localStorage.removeItem('authToken');
        localStorage.removeItem('user_id');
      }
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  return { user, loading };
}
