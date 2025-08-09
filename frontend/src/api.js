const API_BASE = import.meta.env.VITE_API_BASE || "";

async function handleJson(res) {
  if (!res.ok) {
    let msg = `Request failed: ${res.status}`;
    let code;
    try {
      const data = await res.json();
      if (typeof data.detail === 'string') {
        msg = data.detail;
      } else if (data.detail && typeof data.detail === 'object') {
        msg = data.detail.message || data.detail.error || JSON.stringify(data.detail);
        code = data.detail.error;
      }
    } catch {}
    if (!code && res.status === 409) {
      code = 'daily_quota_exceeded';
    }
    const err = new Error(msg);
    if (code) err.code = code;
    throw err;
  }
  return res.json();
}

function authHeaders() {
  const token =
    typeof localStorage !== 'undefined' ? localStorage.getItem('authToken') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getQuizStart(setId, lang) {
  let url = setId ? `${API_BASE}/quiz/start?set_id=${setId}` : `${API_BASE}/quiz/start`;
  if (lang) {
    url += (url.includes('?') ? `&lang=${lang}` : `?lang=${lang}`);
  }
  const res = await fetch(url, { headers: { ...authHeaders() } });
  return handleJson(res);
}

export async function submitQuiz(sessionId, answers) {
  const payload = { session_id: sessionId, answers };
  const res = await fetch(`${API_BASE}/quiz/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(payload)
  });
  return handleJson(res);
}

export async function abandonQuiz(sessionId) {
  try {
    await fetch(`${API_BASE}/quiz/abandon`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ session_id: sessionId })
    });
  } catch {
    // fire and forget
  }
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

export async function setNationality(userId, nationality) {
  const res = await fetch(`${API_BASE}/user/nationality`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ user_id: userId, nationality })
  });
  return handleJson(res);
}

export async function registerAccount({ username, email, password, ref }) {
  const payload = { username, email, password };
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await handleJson(res);
  if (ref && data.token) {
    try {
      await fetch(`${API_BASE}/referral/claim?r=${ref}`, {
        headers: { Authorization: `Bearer ${data.token}` }
      });
    } catch {}
  }
  return data;
}

