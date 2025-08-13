import { createClient } from '@supabase/supabase-js';

function createSafeStorage(): Storage {
  if (typeof window === 'undefined') {
    const map = new Map<string, string>();
    return {
      getItem: (k) => (map.has(k) ? map.get(k)! : null),
      setItem: (k, v) => {
        map.set(k, v);
      },
      removeItem: (k) => {
        map.delete(k);
      },
      clear: () => map.clear(),
      key: (i) => Array.from(map.keys())[i] ?? null,
      get length() {
        return map.size;
      },
    } as Storage;
  }
  return window.localStorage;
}

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL!,
  import.meta.env.VITE_SUPABASE_ANON_KEY!,
  {
    auth: {
      flowType: 'pkce',
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storage: createSafeStorage(),
    },
  },
);

supabase.auth.onAuthStateChange((event, session) => {
  if (import.meta.env.DEV) console.info('[auth]', event, !!session);
});

