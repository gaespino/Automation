/**
 * MCA Single Decoder
 * ==================
 * Decode individual MCA register values for CHA, LLC, CORE, MEMORY, IO, FIRST_ERROR.
 * Supports GNR, CWF, and DMR products.
 */
import { useState } from 'react'
import { mcaApi } from '../../services/api'

const ACCENT = '#ff6b8a'
const REG_TYPES = ['CORE', 'CHA', 'LLC', 'MEMORY', 'IO', 'FIRST_ERROR']
const PRODUCTS   = ['GNR', 'CWF', 'DMR']

export default function MCADecoder() {
  const [register, setRegister] = useState('')
  const [type, setType] = useState('CORE')
  const [product, setProduct] = useState('GNR')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const decode = async () => {
    if (!register.trim()) return
    setLoading(true); setError(''); setResult(null)
    try {
      const r = await mcaApi.decode(register.trim(), type, product)
      setResult(r)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const copyResult = () => {
    if (!result) return
    navigator.clipboard.writeText(JSON.stringify(result, null, 2))
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title" style={{ color: ACCENT }}>MCA Single Decoder</h1>
        <p className="page-subtitle">Decode individual MCA register values — CHA, LLC, CORE, MEMORY, IO, FIRST_ERROR</p>
      </div>

      {/* Input form */}
      <div className="card mb-4" style={{ maxWidth: '640px', borderLeft: `3px solid ${ACCENT}` }}>
        <div className="grid grid-3 mb-4" style={{ gridTemplateColumns: '2fr 1fr 1fr', gap: '1rem' }}>
          <div>
            <label>Register Value (hex)</label>
            <input value={register} onChange={e => setRegister(e.target.value)}
              placeholder="e.g. 0xBE000000010C0151"
              style={{ fontFamily: 'var(--font-mono)' }}
              onKeyDown={e => e.key === 'Enter' && decode()} />
          </div>
          <div>
            <label>Register Type</label>
            <select value={type} onChange={e => setType(e.target.value)}>
              {REG_TYPES.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label>Product</label>
            <select value={product} onChange={e => setProduct(e.target.value)}>
              {PRODUCTS.map(p => <option key={p}>{p}</option>)}
            </select>
          </div>
        </div>
        <button className="btn w-full" onClick={decode} disabled={loading}
          style={{ background: ACCENT, color: '#000', border: 'none', fontWeight: 700 }}>
          {loading ? 'Decoding…' : 'Decode Register'}
        </button>
        {error && <p style={{ color: 'var(--accent-danger)', marginTop: '0.75rem', fontSize: '0.85rem' }}>{error}</p>}
      </div>

      {/* Result */}
      {result && (
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <div className="flex justify-between items-center mb-4">
            <div>
              <span style={{ color: ACCENT, fontWeight: 700 }}>{result.type}</span>
              <span style={{ color: '#555', margin: '0 0.5rem' }}>·</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: '#e0e0e0' }}>{result.raw}</span>
              <span style={{ marginLeft: '0.75rem' }}>
                {result.valid
                  ? <span className="badge badge-success">Valid</span>
                  : <span className="badge badge-muted">Not Valid</span>}
                {result.uncorrected && <span className="badge badge-danger ms-1">Uncorrected</span>}
              </span>
            </div>
            <button className="btn btn-outline btn-sm" onClick={copyResult}>Copy JSON</button>
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.83rem' }}>
            <thead>
              <tr style={{ color: '#a0a0a0', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                {['Field','Bits','Value (Hex)','Value (Dec)','Description'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '0.35rem 0.6rem', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.fields.map(f => (
                <tr key={f.name} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '0.35rem 0.6rem', color: ACCENT, fontWeight: 600 }}>{f.name}</td>
                  <td style={{ padding: '0.35rem 0.6rem', color: '#a0a0a0', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>{f.bits}</td>
                  <td style={{ padding: '0.35rem 0.6rem', color: '#e0e0e0', fontFamily: 'var(--font-mono)' }}>{f.hex}</td>
                  <td style={{ padding: '0.35rem 0.6rem', color: '#a0a0a0', fontFamily: 'var(--font-mono)' }}>{f.value}</td>
                  <td style={{ padding: '0.35rem 0.6rem', color: '#777', fontSize: '0.78rem' }}>{f.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
