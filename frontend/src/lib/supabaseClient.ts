import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL!,
  import.meta.env.VITE_SUPABASE_ANON_KEY!,
  {
    auth: {
      flowType: 'pkce',
      detectSessionInUrl: true,
      autoRefreshToken: true,
      persistSession: true,
      storage: window.localStorage,
    },
  }
);

supabase.auth.onAuthStateChange((event, session) => {
  if (import.meta.env.DEV) console.info('[auth]', event, !!session);
});
