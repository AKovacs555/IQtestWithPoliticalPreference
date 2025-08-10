import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabaseClient';
import { fetchWithAuth } from '../api';

export function useAuth() {
  const [user, setUser] = useState<any>(null);
  // ユーザー情報を取得中かどうかを示すフラグ
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 初回マウント時にセッションを取得
    (async () => {
      const { data } = await supabase.auth.getSession();
      const session = data?.session;
      setUser(session?.user ?? null);
      if (session?.access_token) {
        localStorage.setItem('authToken', session.access_token);
      }
      if (session?.user?.id) {
        localStorage.setItem('user_id', session.user.id);
      }
      // セッション取得が完了したので loading を解除
      setLoading(false);
    })();

    const { data: sub } = supabase.auth.onAuthStateChange((event, session) => {
      if (session?.user) {
        setUser(session.user);
        if (session.access_token) {
          localStorage.setItem('authToken', session.access_token);
        }
        if (session.user?.id) {
          localStorage.setItem('user_id', session.user.id);
          if (event === 'SIGNED_IN') {
            // Ensure we have a row in public.app_users on first sign in
            const pending = localStorage.getItem('pending_username');
            const body: any = { user_id: session.user.id };
            if (pending) body.username = pending;
            fetchWithAuth('/auth/upsert_user', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(body)
            })
              .then(() => {
                if (pending) localStorage.removeItem('pending_username');
              })
              .catch(() => {});
          }
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
