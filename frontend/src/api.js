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

export async function getQuizStart(setId) {
  const url = setId ? `${API_BASE}/quiz/start?set_id=${setId}` : `${API_BASE}/quiz/start`;
  const res = await fetch(url);
  return handleJson(res);
}

export async function submitQuiz(sessionId, answers) {
  const res = await fetch(`${API_BASE}/quiz/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, answers })
  });
  return handleJson(res);
}

export async function getSurvey() {
  const res = await fetch(`${API_BASE}/survey/start`);
  return handleJson(res);
}

export async function submitSurvey(answers) {
  const res = await fetch(`${API_BASE}/survey/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers })
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, party_ids: partyIds })
  });
  if (!res.ok) {
    const { detail } = await res.json();
    throw new Error(detail || 'Party selection failed');
  }
  return true;
}

