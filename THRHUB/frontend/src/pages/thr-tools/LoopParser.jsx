/**
 * PTC Loop Parser
 * ===============
 * Paste or upload PTC loop log content, extract pass/fail summary and MCA entries.
 */
import { useState } from 'react'
import { loopParserApi } from '../../services/api'

const ACCENT = '#00d4ff'
const PRODUCTS = ['GNR', 'CWF', 'DMR']

export default function LoopParser() {
  const [content, setContent] = useState('')
  const [product, setProduct] = useState('GNR')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const parse = async () => {
    if (!content.trim()) return
    setLoading(true); setError(''); setResult(null)
    try {
      const r = await loopParserApi.parse(content, product)
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

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title" style={{ color: ACCENT }}>PTC Loop Parser</h1>
        <p className="page-subtitle">Parse loop log content and extract pass/fail data and MCA entries</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Input */}
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <div className="flex justify-between items-center mb-2">
            <h4 style={{ color: ACCENT }}>Log Content</h4>
            <div className="flex gap-2 items-center">
              <select value={product} onChange={e => setProduct(e.target.value)}
                style={{ background: '#1a1d26', border: '1px solid rgba(255,255,255,0.08)', color: '#e0e0e0',
                  borderRadius: '5px', padding: '0.2rem 0.4rem', fontSize: '0.8rem', width: 'auto' }}>
                {PRODUCTS.map(p => <option key={p}>{p}</option>)}
              </select>
              <label className="btn btn-outline btn-sm" style={{ cursor: 'pointer', marginBottom: 0 }}>
                Load File
                <input type="file" accept=".txt,.log" onChange={handleFile} style={{ display: 'none' }} />
              </label>
            </div>
          </div>
          <textarea value={content} onChange={e => setContent(e.target.value)}
            rows={18} placeholder="Paste PTC loop log content here..."
            style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
              background: '#0e1016', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px',
              color: '#a0a0a0', padding: '0.75rem', resize: 'vertical' }} />
          <button className="btn w-full mt-2" onClick={parse} disabled={loading}
            style={{ background: ACCENT, color: '#000', border: 'none', fontWeight: 700 }}>
            {loading ? 'Parsing…' : 'Parse Log'}
          </button>
          {error && <p style={{ color: 'var(--accent-danger)', marginTop: '0.5rem', fontSize: '0.83rem' }}>{error}</p>}
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {result ? (
            <>
              {/* Summary stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '0.75rem' }}>
                {[
                  { label: 'Total Loops', value: result.total_loops, accent: '#00d4ff' },
                  { label: 'Passed',      value: result.passed,      accent: '#00ff9d' },
                  { label: 'Failed',      value: result.failed,      accent: '#ff4d4d' },
                  { label: 'Pass Rate',   value: result.pass_rate,   accent: '#ffbd2e' },
                ].map(s => (
                  <div key={s.label} className="stat-card">
                    <div className="stat-label">{s.label}</div>
                    <div className="stat-value" style={{ color: s.accent, fontSize: '1.5rem' }}>{s.value}</div>
                  </div>
                ))}
              </div>

              {/* Loop results */}
              {result.loops.length > 0 && (
                <div className="card" style={{ borderLeft: `3px solid ${ACCENT}`, maxHeight: '280px', overflowY: 'auto' }}>
                  <h5 style={{ color: ACCENT, marginBottom: '0.5rem' }}>Loops ({result.loops.length})</h5>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                    {result.loops.map(l => (
                      <span key={l.loop} className={`badge ${l.result === 'PASS' ? 'badge-success' : 'badge-danger'}`}>
                        #{l.loop} {l.result}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* MCA entries */}
              {result.mcas.length > 0 && (
                <div className="card" style={{ borderLeft: '3px solid #ff4d4d', maxHeight: '280px', overflowY: 'auto' }}>
                  <h5 style={{ color: '#ff4d4d', marginBottom: '0.5rem' }}>MCA Entries ({result.mcas.length})</h5>
                  {result.mcas.map((m, i) => (
                    <div key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: '#ff6b8a', marginBottom: '0.2rem' }}>
                      Bank {m.bank}: {m.value}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px' }}>
              <p className="text-muted">Parse a log to see results here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
