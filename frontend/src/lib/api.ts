import { supabase } from './supabaseClient';

export async function fetchWithAuth(path: string, init: RequestInit = {}) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  console.log('[API] Fetching', path, 'with token', token ? token.slice(0, 8) : 'NONE');
  const headers = new Headers(init.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const base = import.meta.env.VITE_API_BASE || window.location.origin;
  return fetch(`${base}${path}`, { ...init, headers });
}

export async function fetchProfile() {
  const res = await fetchWithAuth('/user/profile');
  if (!res.ok) throw new Error(String(res.status));
  return res.json() as Promise<{ id: string; email?: string; username?: string; is_admin: boolean }>;
}

export interface SurveyOptionInput {
  text: string;
  is_exclusive?: boolean;
  requires_text?: boolean;
  order: number;
}

export interface SurveyPayload {
  title: string;
  question_text: string;
  language: string;
  allowed_countries: string[];
  selection_type: 'single' | 'multiple';
  status?: 'pending' | 'approved';
  options: SurveyOptionInput[];
  auto_translate?: boolean;
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
  return res.json();
}

export async function updateSurvey(id: string, payload: SurveyPayload) {
  const res = await fetchWithAuth(`/admin/surveys/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}

export async function deleteSurvey(id: string) {
  const res = await fetchWithAuth(`/admin/surveys/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}

export async function getAvailableSurveys(lang: string, country: string) {
  const res = await fetchWithAuth(
    `/surveys/available?lang=${encodeURIComponent(lang)}&country=${encodeURIComponent(country)}`
  );
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}

export async function respondSurvey(
  surveyId: string,
  optionIds: string[],
  otherTexts: Record<string, string>
) {
  const res = await fetchWithAuth(`/surveys/${surveyId}/respond`, {
    method: 'POST',
    body: JSON.stringify({ option_ids: optionIds, other_texts: otherTexts }),
  });
  if (!res.ok) throw new Error(String(res.status));
  return res.text();
}

export async function getSurveyStats(surveyId: string) {
  const res = await fetchWithAuth(`/surveys/${surveyId}/stats`);
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}
