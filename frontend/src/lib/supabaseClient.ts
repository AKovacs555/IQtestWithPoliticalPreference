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

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL!;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY!;

// 明示的に PKCE + detectSessionInUrl を有効化。自動更新＋永続化もオン
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    flowType: 'pkce',
    detectSessionInUrl: true,
    persistSession: true,
    autoRefreshToken: true,
    storage: createSafeStorage(),
  },
});

supabase.auth.onAuthStateChange((event, session) => {
  if (import.meta.env.DEV) console.info('[auth]', event, !!session);
});

