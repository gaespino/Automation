/**
 * Fuse File Generator
 * ====================
 * Parse fuse CSV data and filter by product/IP. Generate .fuse output.
 */
import { useState } from 'react'
import { fuseApi } from '../../services/api'

const ACCENT = '#ff9f45'
const PRODUCTS = ['GNR', 'CWF', 'DMR']

export default function FuseGenerator() {
  const [content, setContent] = useState('')
  const [product, setProduct] = useState('GNR')
  const [ipFilter, setIpFilter] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const parse = async () => {
    if (!content.trim()) return
    setLoading(true); setError(''); setResult(null)
    try {
      const r = await fuseApi.parse(content, product, ipFilter)
      setResult(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFile = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => setContent(ev.target.result)
    reader.readAsText(file)
    e.target.value = ''
  }

  const exportFuse = () => {
    if (!result?.fuses) return
    const lines = result.fuses.map(f => Object.values(f).join(','))
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `${product}_fuses.csv`; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title" style={{ color: ACCENT }}>⚡ Fuse File Generator</h1>
        <p className="page-subtitle">Parse and filter fuse CSV data — generate product-specific fuse configuration files</p>
      </div>

      {/* Controls */}
      <div className="card mb-4" style={{ borderLeft: `3px solid ${ACCENT}` }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '1rem', alignItems: 'end' }}>
          <div>
            <label>Product</label>
            <select value={product} onChange={e => setProduct(e.target.value)}>
              {PRODUCTS.map(p => <option key={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label>IP Filter (optional)</label>
            <input value={ipFilter} onChange={e => setIpFilter(e.target.value)} placeholder="e.g. CORE, LLC" />
          </div>
          <div>
            <label>Load CSV File</label>
            <label className="btn btn-outline w-full" style={{ cursor: 'pointer' }}>
              Browse
              <input type="file" accept=".csv,.txt" onChange={handleFile} style={{ display: 'none' }} />
            </label>
          </div>
          <button className="btn" onClick={parse} disabled={loading}
            style={{ background: ACCENT, color: '#000', border: 'none', fontWeight: 700 }}>
            {loading ? 'Parsing…' : 'Parse'}
          </button>
        </div>
        {error && <p style={{ color: 'var(--accent-danger)', marginTop: '0.75rem', fontSize: '0.85rem' }}>{error}</p>}
      </div>

      {/* CSV input */}
      <div className="card mb-4" style={{ borderLeft: `3px solid ${ACCENT}` }}>
        <div className="flex justify-between items-center mb-2">
          <span style={{ color: ACCENT, fontWeight: 600 }}>CSV Content</span>
          {result && <span className="badge badge-info">{result.count} fuses matched</span>}
        </div>
        <textarea value={content} onChange={e => setContent(e.target.value)}
          rows={8} placeholder="Paste CSV fuse data here (name,value,...)"
          style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
            background: '#0e1016', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px',
            color: '#a0a0a0', padding: '0.75rem', resize: 'vertical' }} />
      </div>

      {/* Results */}
      {result && (
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <div className="flex justify-between items-center mb-4">
            <h4 style={{ color: ACCENT }}>Results — {result.count} fuse entries</h4>
            <button className="btn btn-outline btn-sm" onClick={exportFuse}>↓ Export CSV</button>
          </div>
          <div style={{ overflowX: 'auto', maxHeight: '400px', overflowY: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
              {result.fuses.length > 0 && (
                <>
                  <thead>
                    <tr style={{ color: '#a0a0a0', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                      {Object.keys(result.fuses[0]).map(k => (
                        <th key={k} style={{ textAlign: 'left', padding: '0.3rem 0.5rem', fontWeight: 500 }}>{k}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.fuses.map((f, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        {Object.values(f).map((v, j) => (
                          <td key={j} style={{ padding: '0.3rem 0.5rem', color: '#e0e0e0', fontFamily: 'var(--font-mono)' }}>{v}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </>
              )}
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
