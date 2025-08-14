/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE: string;
  readonly VITE_SUPABASE_URL: string;
  readonly VITE_SUPABASE_ANON_KEY: string;
  readonly VITE_DEFAULT_PHONE_COUNTRY?: string;
  readonly VITE_ENABLED_B_EXTRAS?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
