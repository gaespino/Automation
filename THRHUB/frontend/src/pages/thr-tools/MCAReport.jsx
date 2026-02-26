/**
 * PPV MCA Report
 * ==============
 * Generate MCA reports from Bucketer files or S2T Logger data.
 * Frontend stub — paste bucketer output, generate summary.
 */
import { useState } from 'react'
import { mcaApi } from '../../services/api'

const ACCENT = '#ff4d4d'
const PRODUCTS = ['GNR', 'CWF', 'DMR']

export default function MCAReport() {
  const [lines, setLines] = useState('')
  const [product, setProduct] = useState('GNR')
  const [decoded, setDecoded] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Parse hex values from pasted text and decode each
  const generate = async () => {
    setLoading(true); setError(''); setDecoded([])
    const hexPattern = /0x[0-9A-Fa-f]{8,16}/g
    const matches = [...(lines.match(hexPattern) || [])]
    if (!matches.length) { setError('No hex MCA values found in input.'); setLoading(false); return }

    try {
      const results = await Promise.all(
        matches.slice(0, 50).map(h => mcaApi.decode(h, 'CORE', product))
      )
      setDecoded(results.filter(Boolean))
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
    reader.onload = ev => setLines(ev.target.result)
    reader.readAsText(file)
    e.target.value = ''
  }

  const exportReport = () => {
    if (!decoded.length) return
    const txt = decoded.map(r =>
      `${r.raw} | Valid:${r.valid} | UC:${r.uncorrected}\n` +
      r.fields.map(f => `  ${f.name.padEnd(20)} ${f.bits.padEnd(8)} ${f.hex}`).join('\n')
    ).join('\n\n')
    const blob = new Blob([txt], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `mca_report_${product}.txt`; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title" style={{ color: ACCENT }}>PPV MCA Report</h1>
        <p className="page-subtitle">Generate MCA reports from bucketer output or S2T Logger data</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        {/* Input */}
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <div className="flex justify-between items-center mb-2">
            <h4 style={{ color: ACCENT }}>Input Data</h4>
            <div className="flex gap-2 items-center">
              <select value={product} onChange={e => setProduct(e.target.value)}
                style={{ background: '#1a1d26', border: '1px solid rgba(255,255,255,0.08)', color: '#e0e0e0',
                  borderRadius: '5px', padding: '0.2rem 0.4rem', fontSize: '0.8rem', width: 'auto' }}>
                {PRODUCTS.map(p => <option key={p}>{p}</option>)}
              </select>
              <label className="btn btn-outline btn-sm" style={{ cursor: 'pointer', marginBottom: 0 }}>
                Load File
                <input type="file" accept=".txt,.log,.csv" onChange={handleFile} style={{ display: 'none' }} />
              </label>
            </div>
          </div>
          <textarea value={lines} onChange={e => setLines(e.target.value)}
            rows={16} placeholder="Paste bucketer output or S2T Logger data with MCA hex values..."
            style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
              background: '#0e1016', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px',
              color: '#a0a0a0', padding: '0.75rem', resize: 'vertical' }} />
          <button className="btn w-full mt-2" onClick={generate} disabled={loading}
            style={{ background: ACCENT, color: '#fff', border: 'none', fontWeight: 700 }}>
            {loading ? 'Generating…' : 'Generate Report'}
          </button>
          {error && <p style={{ color: 'var(--accent-danger)', marginTop: '0.5rem', fontSize: '0.83rem' }}>{error}</p>}
        </div>

        {/* Report */}
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}`, overflowY: 'auto', maxHeight: '600px' }}>
          <div className="flex justify-between items-center mb-4">
            <h4 style={{ color: ACCENT }}>MCA Report ({decoded.length})</h4>
            {decoded.length > 0 && (
              <button className="btn btn-outline btn-sm" onClick={exportReport}>↓ Export TXT</button>
            )}
          </div>
          {decoded.length === 0 ? (
            <p className="text-muted" style={{ textAlign: 'center', marginTop: '2rem' }}>
              Report will appear here after generation
            </p>
          ) : decoded.map((r, i) => (
            <div key={i} className="card mb-2" style={{
              borderLeft: `2px solid ${r.uncorrected ? '#ff4d4d' : r.valid ? '#00ff9d' : '#555'}`
            }}>
              <div className="flex items-center gap-2 mb-1">
                <span style={{ fontFamily: 'var(--font-mono)', color: '#e0e0e0', fontSize: '0.82rem' }}>{r.raw}</span>
                {r.valid
                  ? <span className="badge badge-success">Valid</span>
                  : <span className="badge badge-muted">Invalid</span>}
                {r.uncorrected && <span className="badge badge-danger">UC</span>}
              </div>
              {r.fields.slice(0, 4).map(f => (
                <div key={f.name} style={{ fontSize: '0.75rem', color: '#666' }}>
                  {f.name}: <span style={{ color: '#a0a0a0', fontFamily: 'var(--font-mono)' }}>{f.hex}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
