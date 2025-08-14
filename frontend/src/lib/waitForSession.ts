import { supabase } from './supabaseClient';
import type { Session } from '@supabase/supabase-js';

/**
 * Supabase セッションが確定するまで待つ。
 * - onAuthStateChange(SIGNED_IN/TOKEN_REFRESHED/USER_UPDATED) と
 *   getSession() のポーリングを併用。
 */
export async function waitForSession(timeoutMs = 7000): Promise<Session> {
  const first = await supabase.auth.getSession();
  if (first.data.session) return first.data.session;

  return new Promise<Session>((resolve, reject) => {
    let done = false;
    const started = Date.now();

    const clearAll = (sub?: { unsubscribe: () => void }, tm?: number) => {
      if (sub) sub.unsubscribe();
      if (tm) clearInterval(tm);
    };

    const tick = async () => {
      if (done) return;
      const now = Date.now();
      if (now - started > timeoutMs) {
        done = true;
        clearAll(subscription, timer);
        return reject(new Error('waitForSession: timeout'));
      }
      const { data } = await supabase.auth.getSession();
      if (data.session) {
        done = true;
        clearAll(subscription, timer);
        resolve(data.session);
      }
    };

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (done) return;
      if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED' || event === 'USER_UPDATED') {
        if (session) {
          done = true;
          clearAll(subscription, timer);
          resolve(session);
        }
      }
    });

    // 150ms 間隔で安全側ポーリング
    const timer = setInterval(tick, 150);
  });
}
