import { supabase } from './lib/supabaseClient';

const API_BASE = import.meta.env.VITE_API_BASE || '';

async function authHeaders() {
  try {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers || {});
  const extra = await authHeaders();
  Object.entries(extra).forEach(([k, v]) => headers.set(k, String(v)));
  if (!headers.has('Content-Type') && init.body) headers.set('Content-Type', 'application/json');
  return fetch(`${API_BASE}${path}`, { ...init, headers, credentials: 'include' });
}

export async function apiGet<T = unknown>(path: string): Promise<T> {
  const res = await apiFetch(path, { method: 'GET' });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export async function apiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await apiFetch(path, { method: 'POST', body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export async function apiDelete<T = unknown>(path: string): Promise<T> {
  const res = await apiFetch(path, { method: 'DELETE' });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export async function getProfile() {
  return apiGet('/user/profile');
}

export async function updateProfile(data: unknown) {
  return apiPost('/user/profile', data);
}

export async function getQuizStart(setId?: string | null, lang?: string | null) {
  let url = '/quiz/start';
  const params = new URLSearchParams();
  if (setId) params.set('set_id', setId);
  if (lang) params.set('lang', lang);
  if (Array.from(params).length) url += `?${params.toString()}`;
  return apiGet(url);
}

export async function submitQuiz(sessionId: string, answers: unknown) {
  return apiPost('/quiz/submit', { session_id: sessionId, answers });
}

export async function abandonQuiz(sessionId: string) {
  try {
    await apiPost('/quiz/abandon', { session_id: sessionId });
  } catch {
    // fire and forget
  }
}

export async function getSurvey(lang?: string | null, userId?: string | null, nationality?: string | null) {
  let url = '/survey/start';
  const params = new URLSearchParams();
  if (lang) params.set('lang', lang);
  if (userId) params.set('user_id', userId);
  if (nationality) params.set('nationality', nationality);
  if (Array.from(params).length) url += `?${params.toString()}`;
  return apiGet(url);
}

export async function submitSurvey(answers: unknown, userId?: string | null) {
  const payload: any = { answers };
  if (userId) payload.user_id = userId;
  return apiPost('/survey/submit', payload);
}

export async function completeSurvey(userId?: string | null) {
  return apiPost('/survey/complete', { user_id: userId });
}

export async function setNationality(userId: string, nationality: string) {
  return apiPost('/user/nationality', { user_id: userId, nationality });
}

export async function registerAccount({ username, email, password, ref }: { username: string; email: string; password: string; ref?: string; }) {
  const payload = { username, email, password };
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  const data = await res.json();
  if (ref && data.token) {
    try {
      await fetch(`${API_BASE}/referral/claim?r=${ref}`, {
        headers: { Authorization: `Bearer ${data.token}` },
      });
    } catch {
      // ignore referral errors
    }
  }
  return data;
}

