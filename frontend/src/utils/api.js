export async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error('API error');
  return res.json();
}
