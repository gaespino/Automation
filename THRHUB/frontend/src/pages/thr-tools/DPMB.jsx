/**
 * DPMB Requests
 * =============
 * Interface for Bucketer data requests through DPMB API.
 * Provides a query builder UI — product, VID, WW, bucket, test.
 */
import { useState } from 'react'

const ACCENT = '#7000ff'
const PRODUCTS = ['GNR', 'CWF', 'DMR']
const ENVS = ['SLT', 'CHx', 'SORT', 'CLASS', 'FINAL']

export default function DPMB() {
  const [form, setForm] = useState({ product: 'GNR', environment: 'SLT', vid: '', ww: '', bucket: '', test: '' })
  const [queries, setQueries] = useState([])
  const [toast, setToast] = useState(null)

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const addQuery = () => {
    if (!form.vid && !form.bucket) { showToast('Provide at least VID or Bucket.', 'error'); return }
    setQueries(q => [...q, { ...form, id: Date.now() }])
    showToast('Query added to queue.')
  }

  const exportCSV = () => {
    if (!queries.length) return
    const header = Object.keys(queries[0]).filter(k => k !== 'id').join(',')
    const rows = queries.map(q => Object.entries(q).filter(([k]) => k !== 'id').map(([, v]) => v).join(','))
    const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'dpmb_queries.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page-container">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
      <div className="page-header">
        <h1 className="page-title" style={{ color: ACCENT }}>DPMB Requests</h1>
        <p className="page-subtitle">Build and queue Bucketer data requests for DPMB API</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1rem' }}>
        {/* Query builder */}
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <h4 style={{ color: ACCENT, marginBottom: '1rem' }}>Query Builder</h4>

          <label>Product</label>
          <select value={form.product} onChange={e => set('product', e.target.value)} className="mb-2">
            {PRODUCTS.map(p => <option key={p}>{p}</option>)}
          </select>

          <label>Environment</label>
          <select value={form.environment} onChange={e => set('environment', e.target.value)} className="mb-2">
            {ENVS.map(e => <option key={e}>{e}</option>)}
          </select>

          <label>Visual ID (VID)</label>
          <input value={form.vid} onChange={e => set('vid', e.target.value)}
            placeholder="e.g. A1B2C3" className="mb-2" />

          <label>Work Week</label>
          <input value={form.ww} onChange={e => set('ww', e.target.value)}
            placeholder="e.g. 2026WW01" className="mb-2" />

          <label>Bucket</label>
          <input value={form.bucket} onChange={e => set('bucket', e.target.value)}
            placeholder="e.g. 3STRIKE" className="mb-2" />

          <label>Test</label>
          <input value={form.test} onChange={e => set('test', e.target.value)}
            placeholder="e.g. MeshTest_001" className="mb-4" />

          <button className="btn w-full" onClick={addQuery}
            style={{ background: ACCENT, color: '#fff', border: 'none', fontWeight: 700 }}>
            + Add to Queue
          </button>
        </div>

        {/* Queue */}
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <div className="flex justify-between items-center mb-4">
            <h4 style={{ color: ACCENT }}>Request Queue ({queries.length})</h4>
            <div className="flex gap-2">
              <button className="btn btn-outline btn-sm" onClick={exportCSV} disabled={!queries.length}>↓ Export CSV</button>
              <button className="btn btn-danger btn-sm" onClick={() => setQueries([])} disabled={!queries.length}>Clear</button>
            </div>
          </div>

          {queries.length === 0 ? (
            <p className="text-muted" style={{ textAlign: 'center', marginTop: '2rem' }}>
              No queries queued. Use the builder to add requests.
            </p>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ color: '#a0a0a0', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                  {['#','Product','Env','VID','WW','Bucket','Test'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '0.35rem 0.5rem', fontWeight: 500 }}>{h}</th>
                  ))}
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {queries.map((q, i) => (
                  <tr key={q.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '0.35rem 0.5rem', color: '#555' }}>{i + 1}</td>
                    <td style={{ padding: '0.35rem 0.5rem' }}><span className="badge badge-info">{q.product}</span></td>
                    <td style={{ padding: '0.35rem 0.5rem', color: '#a0a0a0' }}>{q.environment}</td>
                    <td style={{ padding: '0.35rem 0.5rem', fontFamily: 'var(--font-mono)', color: '#e0e0e0' }}>{q.vid || '—'}</td>
                    <td style={{ padding: '0.35rem 0.5rem', color: '#a0a0a0' }}>{q.ww || '—'}</td>
                    <td style={{ padding: '0.35rem 0.5rem', color: '#a0a0a0' }}>{q.bucket || '—'}</td>
                    <td style={{ padding: '0.35rem 0.5rem', color: '#a0a0a0', fontSize: '0.75rem' }}>{q.test || '—'}</td>
                    <td style={{ padding: '0.35rem 0.5rem' }}>
                      <button onClick={() => setQueries(qs => qs.filter(x => x.id !== q.id))}
                        style={{ background: 'none', border: 'none', color: '#ff4d4d', cursor: 'pointer', fontSize: '0.75rem' }}>✕</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
