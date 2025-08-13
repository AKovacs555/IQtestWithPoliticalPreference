import { Session } from '@supabase/supabase-js';
import { supabase } from './supabaseClient';

export async function waitForSession(timeoutMs: number): Promise<Session | null> {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const { data } = await supabase.auth.getSession();
    if (data.session) {
      return data.session;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error('timeout');
}
