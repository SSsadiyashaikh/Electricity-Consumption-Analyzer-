// All calls go to Flask through the Vite proxy (/api -> http://127.0.0.1:5000/api).
const BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options) {
  let res
  try {
    res = await fetch(BASE + path, options)
  } catch {
    throw new Error('Cannot reach the backend. Start it with start_project.bat (or: python app.py in backend/).')
  }
  let body = null
  try { body = await res.json() } catch { /* non-JSON response */ }
  if (!res.ok) {
    const msg = (body && body.error) || `Request failed (${res.status})`
    throw new Error(body && body.hint ? `${msg} ${body.hint}` : msg)
  }
  return body
}

const post = (path, data) => request(path, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})

export const api = {
  health: () => request('/health'),
  summary: () => request('/summary'),
  monthly: () => request('/history?granularity=monthly'),
  metrics: () => request('/model-metrics'),
  predict: (data) => post('/predict', data),
  classify: (data) => post('/classify', data),
  cluster: (data) => post('/cluster', data),
}
