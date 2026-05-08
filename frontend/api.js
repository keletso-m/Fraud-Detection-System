const BASE = '';

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health:             ()       => request('GET',  '/health'),
  getIncidents:       (params) => request('GET',  `/incidents${params ? '?' + new URLSearchParams(params) : ''}`),
  getIncident:        (id)     => request('GET',  `/incidents/${id}`),
  postActivity:       (data)   => request('POST', '/events/activity',     data),
  postTransaction:    (data)   => request('POST', '/events/transaction',  data),
};