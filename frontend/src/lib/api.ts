import { supabase } from './supabaseClient';

export async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data?.session?.access_token ?? localStorage.getItem('authToken');
}

export async function fetchWithAuth(path: string, init: RequestInit = {}) {
  const token = await getAccessToken();
  const headers = new Headers(init.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const base = import.meta.env.VITE_API_BASE!;
  return fetch(`${base}${path}`, { ...init, headers });
}

export async function fetchProfile() {
  const res = await fetchWithAuth('/user/profile');
  if (!res.ok) throw new Error(String(res.status));
  return res.json() as Promise<{ id: string; email?: string; username?: string; is_admin: boolean }>;
}
