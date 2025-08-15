import { supabase } from './lib/supabaseClient';

const API_BASE = import.meta.env.VITE_API_BASE || window.location.origin;

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
  const token = (extra.Authorization || '').replace(/^Bearer\s+/i, '');
  if (import.meta.env.DEV) {
    // eslint-disable-next-line no-console
    console.log('[api] ->', API_BASE + path, 'token=', token ? `${token.slice(0, 10)}...` : 'NONE');
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers, credentials: 'include' });
  if (!res.ok) {
    const txt = await res.text().catch(() => '');
    if (import.meta.env.DEV) {
      // eslint-disable-next-line no-console
      console.error('[api] !', res.status, txt);
    }
    throw new Error(`API ${res.status}: ${txt}`);
  }
  return res;
}

export async function apiGet<T = unknown>(path: string): Promise<T> {
  const res = await apiFetch(path, { method: 'GET' });
  return res.json();
}

export async function apiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await apiFetch(path, { method: 'POST', body: JSON.stringify(body) });
  return res.json();
}

export async function apiDelete<T = unknown>(path: string): Promise<T> {
  const res = await apiFetch(path, { method: 'DELETE' });
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

export async function submitQuiz(sessionId: string, answers: unknown, surveys?: unknown) {
  return apiPost('/quiz/submit', { session_id: sessionId, answers, surveys });
}

export async function abandonQuiz(sessionId: string) {
  try {
    await apiPost('/quiz/abandon', { session_id: sessionId });
  } catch {
    // fire and forget
  }
}

export async function getAvailableSurveys(lang: string, country: string) {
  const params = new URLSearchParams({ lang, country });
  return apiGet(`/surveys/available?${params.toString()}`);
}

export async function respondSurvey(
  surveyId: string,
  optionIds: string[],
  otherTexts: Record<string, string>
) {
  return apiPost(`/surveys/${surveyId}/respond`, {
    option_ids: optionIds,
    other_texts: otherTexts,
  });
}

export async function getSurveyStats(surveyId: string) {
  return apiGet(`/surveys/${surveyId}/stats`);
}

// Legacy wrappers ---------------------------------------------------------
// The old survey interface exposed start/submit/complete endpoints. They are
// kept here as thin shims so older components compile while the UI migrates to
// the new poll workflow.

export async function getSurvey(lang?: string | null, userId?: string | null, nationality?: string | null) {
  const list = await getAvailableSurveys(lang || 'en', nationality || '');
  return { items: list } as any;
}

export async function submitSurvey(answers: unknown, userId?: string | null) {
  // The legacy caller bundled all answers in one request. The new API submits
  // per-survey responses, so this is a no-op placeholder.
  return {} as any;
}

export async function completeSurvey(userId?: string | null) {
  return {} as any;
}

export async function setNationality(userId: string, nationality: string) {
  return apiPost('/user/nationality', { user_id: userId, nationality });
}

