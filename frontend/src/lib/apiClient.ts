import { supabase } from './supabaseClient';

const API_BASE = import.meta.env.VITE_API_BASE || window.location.origin;
const cache = new Map<string, { data: any; ts: number }>();
const TTL = 30_000;

async function authHeaders(body?: unknown) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  const headers = new Headers();
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  return headers;
}

async function fetchJson(method: string, path: string, body?: unknown, timeout = 8000) {
  const headers = await authHeaders(body);
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal: controller.signal,
    credentials: 'include'
  }).finally(() => clearTimeout(id));
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

async function get(path: string, { revalidate = true, timeout = 8000 } = {}) {
  const cached = cache.get(path);
  const now = Date.now();
  if (cached && now - cached.ts < TTL) {
    if (revalidate) fetchJson('GET', path, undefined, timeout).then(data => cache.set(path, { data, ts: Date.now() })).catch(() => {});
    return cached.data;
  }
  const data = await fetchJson('GET', path, undefined, timeout);
  cache.set(path, { data, ts: Date.now() });
  return data;
}

function post(path: string, body: unknown, { timeout = 8000 } = {}) {
  return fetchJson('POST', path, body, timeout);
}

function del(path: string, { timeout = 8000 } = {}) {
  return fetchJson('DELETE', path, undefined, timeout);
}

export const apiClient = { get, post, delete: del };
