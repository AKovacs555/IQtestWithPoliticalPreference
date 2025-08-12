import { supabase } from './supabaseClient';

export async function fetchWithAuth(path: string, init: RequestInit = {}) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
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

export interface SurveyItemInput {
  label: string;
  is_exclusive?: boolean;
}

export interface SurveyPayload {
  title: string;
  question: string;
  lang: string;
  choice_type: 'sa' | 'ma';
  country_codes: string[];
  items: SurveyItemInput[];
  is_active?: boolean;
}

export async function getSurveys() {
  const res = await fetchWithAuth('/admin/surveys');
  if (!res.ok) throw new Error(String(res.status));
  return res.json() as Promise<{ surveys: any[] }>;
}

export async function createSurvey(payload: SurveyPayload) {
  const res = await fetchWithAuth('/admin/surveys', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(String(res.status));
  return res.json() as Promise<{ id: string }>;
}

export async function updateSurvey(id: string, payload: SurveyPayload) {
  const res = await fetchWithAuth(`/admin/surveys/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(String(res.status));
  return res.json() as Promise<{ updated: boolean }>;
}

export async function deleteSurvey(id: string) {
  const res = await fetchWithAuth(`/admin/surveys/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(String(res.status));
  return res.json() as Promise<{ deleted: boolean }>;
}
