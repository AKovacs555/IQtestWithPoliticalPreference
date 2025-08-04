const API_BASE = import.meta.env.VITE_API_BASE || "";

async function handleJson(res) {
  if (!res.ok) {
    let msg = `Request failed: ${res.status}`;
    try {
      const data = await res.json();
      msg = data.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

function authHeaders() {
  const token =
    typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getQuizStart(setId, lang, userId) {
  let url = setId ? `${API_BASE}/quiz/start?set_id=${setId}` : `${API_BASE}/quiz/start`;
  if (lang) {
    url += (url.includes('?') ? `&lang=${lang}` : `?lang=${lang}`);
  }
  const uid =
    userId || (typeof localStorage !== 'undefined' ? localStorage.getItem('user_id') : null);
  if (uid) {
    url += (url.includes('?') ? `&user_id=${uid}` : `?user_id=${uid}`);
  }
  const res = await fetch(url, { headers: { ...authHeaders() } });
  return handleJson(res);
}

export async function submitQuiz(sessionId, answers, userId) {
  const payload = { session_id: sessionId, answers };
  if (userId) payload.user_id = userId;
  const res = await fetch(`${API_BASE}/quiz/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  });
  return handleJson(res);
}

export async function getSurvey(lang, userId, nationality) {
  let url = `${API_BASE}/survey/start`;
  const params = [];
  if (lang) params.push(`lang=${lang}`);
  const uid =
    userId ||
    (typeof localStorage !== 'undefined'
      ? localStorage.getItem('user_id')
      : null);
  if (uid) params.push(`user_id=${uid}`);
  const nat =
    nationality ||
    (typeof localStorage !== 'undefined'
      ? localStorage.getItem('nationality')
      : null);
  if (nat) params.push(`nationality=${nat}`);
  if (params.length) url += `?${params.join('&')}`;
  const res = await fetch(url, { headers: { ...authHeaders() } });
  return handleJson(res);
}

export async function submitSurvey(answers, userId) {
  const payload = { answers };
  if (userId) payload.user_id = userId;
  const res = await fetch(`${API_BASE}/survey/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  });
  return handleJson(res);
}

export async function completeSurvey(userId) {
  const res = await fetch(`${API_BASE}/survey/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ user_id: userId })
  });
  return handleJson(res);
}

export async function getParties() {
  const { parties } = await getSurvey();
  return parties || [];
}

export async function submitPartySelection(userId, partyIds) {
  const res = await fetch(`${API_BASE}/user/party`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ user_id: userId, party_ids: partyIds })
  });
  if (!res.ok) {
    const { detail } = await res.json();
    throw new Error(detail || 'Party selection failed');
  }
  return true;
}

export async function setNationality(userId, nationality) {
  const res = await fetch(`${API_BASE}/user/nationality`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ user_id: userId, nationality })
  });
  return handleJson(res);
}

export async function getPartiesForCountry(country) {
  const res = await fetch(`${API_BASE}/user/parties/${country}`);
  return handleJson(res);
}

export async function sendCode(phone) {
  const res = await fetch(`${API_BASE}/auth/send-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone })
  });
  return handleJson(res);
}

export async function verifyCode(phone, code) {
  const res = await fetch(`${API_BASE}/auth/verify-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, code })
  });
  return handleJson(res);
}

export async function registerAccount({ phone, email, password, code, ref }) {
  const payload = { phone, email, password, code };
  if (ref) payload.referral_code = ref;
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return handleJson(res);
}

export async function loginAccount(identifier, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identifier, password })
  });
  return handleJson(res);
}

