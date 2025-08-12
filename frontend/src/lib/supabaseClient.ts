function createMemoryStorage(): Storage {
  let store: Record<string, string> = {};
  return {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => {
      store[k] = v;
    },
    removeItem: (k) => {
      delete store[k];
    },
    clear: () => {
      store = {};
    },
    key: (i) => Object.keys(store)[i] ?? null,
    get length() {
      return Object.keys(store).length;
    },
  } as unknown as Storage;
}

function getSafeStorage(): Storage {
  try {
    const t = '__sb_test__';
    window.localStorage.setItem(t, '1');
    window.localStorage.removeItem(t);
    return window.localStorage;
  } catch {
    try {
      const t = '__sb_test__';
      window.sessionStorage.setItem(t, '1');
      window.sessionStorage.removeItem(t);
      return window.sessionStorage;
    } catch {
      return createMemoryStorage();
    }
  }
}

import { createClient } from '@supabase/supabase-js';

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL!,
  import.meta.env.VITE_SUPABASE_ANON_KEY!,
  {
    auth: {
      flowType: 'pkce',
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      storage: getSafeStorage(),
    },
  }
);

supabase.auth.onAuthStateChange((event, session) => {
  if (import.meta.env.DEV) console.info('[auth]', event, !!session);
});
