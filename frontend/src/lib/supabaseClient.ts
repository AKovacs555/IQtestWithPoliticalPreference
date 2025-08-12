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

  const storages = [window.localStorage, window.sessionStorage];
  for (const storage of storages) {
    try {
      const test = '__supa_test__';
      storage.setItem(test, '1');
      storage.removeItem(test);
      return storage;
    } catch {
      /* ignore */
    }
  }

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

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL!,
  import.meta.env.VITE_SUPABASE_ANON_KEY!,
  {
    auth: {
      persistSession: true,
      flowType: 'pkce',
      detectSessionInUrl: false,
      storage: createSafeStorage(),
    },
  },
);
