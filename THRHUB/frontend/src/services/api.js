/**
 * THRHUB API Client
 * Thin wrapper around fetch() for talking to the Flask backend.
 */

const BASE = import.meta.env.VITE_API_BASE || '/api'

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(`${BASE}${path}`, opts)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`)
  return data
}

// ── Config ─────────────────────────────────────────────────────────────────
export const configApi = {
  getProductConfig: (product) => request('GET', `/config/${product}`),
  listProducts: () => request('GET', '/config/'),
}

// ── Dashboard ──────────────────────────────────────────────────────────────
export const dashboardApi = {
  getStats: () => request('GET', '/dashboard/stats'),
  getUnits: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request('GET', `/dashboard/units${qs ? `?${qs}` : ''}`)
  },
  getUnit: (id) => request('GET', `/dashboard/units/${id}`),
  createUnit: (data) => request('POST', '/dashboard/units', data),
  updateUnit: (id, data) => request('PUT', `/dashboard/units/${id}`, data),
  getUnitExperiments: (id) => request('GET', `/dashboard/units/${id}/experiments`),
}

// ── Experiments ────────────────────────────────────────────────────────────
export const experimentsApi = {
  list: () => request('GET', '/tools/experiments'),
  save: (name, experiments) => request('POST', '/tools/experiments', { name, experiments }),
  load: (id) => request('GET', `/tools/experiments/${id}`),
}

// ── Automation Flows ───────────────────────────────────────────────────────
export const flowsApi = {
  list: () => request('GET', '/tools/automation-flows'),
  save: (name, nodes, edges, metadata = {}) =>
    request('POST', '/tools/automation-flows', { name, nodes, edges, metadata }),
  load: (id) => request('GET', `/tools/automation-flows/${id}`),
}

// ── MCA ────────────────────────────────────────────────────────────────────
export const mcaApi = {
  decode: (register, type, product) =>
    request('POST', '/tools/mca/decode', { register, type, product }),
}

// ── Loop Parser ────────────────────────────────────────────────────────────
export const loopParserApi = {
  parse: (content, product) =>
    request('POST', '/tools/loop-parser/parse', { content, product }),
}

// ── Fuse Generator ─────────────────────────────────────────────────────────
export const fuseApi = {
  parse: (content, product, ip_filter) =>
    request('POST', '/tools/fuses/parse', { content, product, ip_filter }),
}
