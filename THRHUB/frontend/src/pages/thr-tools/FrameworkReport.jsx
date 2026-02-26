/**
 * Framework Report Builder
 * ========================
 * Create comprehensive reports from Debug Framework experiment data.
 */
import { useState } from 'react'

const ACCENT = '#00ff9d'
const PRODUCTS = ['GNR', 'CWF', 'DMR']

export default function FrameworkReport() {
  const [units, setUnits] = useState([])
  const [unitForm, setUnitForm] = useState({ vid: '', product: 'GNR', bucket: '', ww: '', status: 'fail', summary: '' })
  const [report, setReport] = useState('')

  const addUnit = () => {
    if (!unitForm.vid) return
    setUnits(u => [...u, { ...unitForm, id: Date.now() }])
    setUnitForm({ vid: '', product: 'GNR', bucket: '', ww: '', status: 'fail', summary: '' })
  }

  const generateReport = () => {
    if (!units.length) return
    const now = new Date().toISOString().slice(0, 19)
    const lines = [
      '══════════════════════════════════════════════════════',
      `  Debug Framework Report — Generated ${now}`,
      '══════════════════════════════════════════════════════',
      '',
      `  Total Units: ${units.length}`,
      `  Failing:     ${units.filter(u => u.status === 'fail').length}`,
      `  Passing:     ${units.filter(u => u.status === 'pass').length}`,
      '',
      '── Unit Details ──────────────────────────────────────',
      '',
      ...units.map((u, i) => [
        `  [${i + 1}] VID: ${u.vid}  Product: ${u.product}  WW: ${u.ww || 'N/A'}`,
        `      Bucket: ${u.bucket || 'N/A'}  Status: ${u.status.toUpperCase()}`,
        u.summary ? `      Summary: ${u.summary}` : null,
        '',
      ].filter(Boolean).join('\n')),
      '══════════════════════════════════════════════════════',
    ]
    setReport(lines.join('\n'))
  }

  const exportTxt = () => {
    if (!report) return
    const blob = new Blob([report], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'framework_report.txt'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title" style={{ color: ACCENT }}>📋 Framework Report Builder</h1>
        <p className="page-subtitle">Create comprehensive reports from Debug Framework experiment data</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1rem' }}>
        {/* Unit input */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
            <h4 style={{ color: ACCENT, marginBottom: '1rem' }}>Add Unit</h4>

            <label>Visual ID *</label>
            <input value={unitForm.vid} onChange={e => setUnitForm(f => ({ ...f, vid: e.target.value }))}
              placeholder="e.g. A1B2C3" className="mb-2" />

            <label>Product</label>
            <select value={unitForm.product} onChange={e => setUnitForm(f => ({ ...f, product: e.target.value }))} className="mb-2">
              {PRODUCTS.map(p => <option key={p}>{p}</option>)}
            </select>

            <label>Work Week</label>
            <input value={unitForm.ww} onChange={e => setUnitForm(f => ({ ...f, ww: e.target.value }))}
              placeholder="e.g. 2026WW05" className="mb-2" />

            <label>Bucket</label>
            <input value={unitForm.bucket} onChange={e => setUnitForm(f => ({ ...f, bucket: e.target.value }))}
              placeholder="e.g. 3STRIKE" className="mb-2" />

            <label>Status</label>
            <select value={unitForm.status} onChange={e => setUnitForm(f => ({ ...f, status: e.target.value }))} className="mb-2">
              {['fail','pass','pending'].map(s => <option key={s}>{s}</option>)}
            </select>

            <label>Summary</label>
            <textarea value={unitForm.summary} onChange={e => setUnitForm(f => ({ ...f, summary: e.target.value }))}
              rows={3} placeholder="Brief failure summary..." className="mb-3"
              style={{ fontFamily: 'var(--font-ui)', fontSize: '0.83rem' }} />

            <button className="btn w-full" onClick={addUnit}
              style={{ background: ACCENT, color: '#000', border: 'none', fontWeight: 700 }}>
              + Add Unit
            </button>
          </div>

          {/* Unit list */}
          <div className="card" style={{ borderLeft: `3px solid ${ACCENT}`, maxHeight: '280px', overflowY: 'auto' }}>
            <div className="flex justify-between items-center mb-2">
              <span style={{ color: ACCENT, fontWeight: 600, fontSize: '0.85rem' }}>Units ({units.length})</span>
              {units.length > 0 && (
                <button className="btn btn-danger btn-sm" onClick={() => { setUnits([]); setReport('') }}>Clear</button>
              )}
            </div>
            {units.map((u, i) => (
              <div key={u.id} style={{
                padding: '0.4rem 0', borderBottom: '1px solid rgba(255,255,255,0.05)',
                fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between',
              }}>
                <div>
                  <span style={{ color: '#e0e0e0', fontFamily: 'var(--font-mono)' }}>{u.vid}</span>
                  <span style={{ color: '#a0a0a0', marginLeft: '0.5rem' }}>[{u.product}]</span>
                  <span className={`badge ${u.status === 'fail' ? 'badge-danger' : 'badge-success'} ms-1`}>{u.status}</span>
                </div>
                <button onClick={() => setUnits(us => us.filter((_, j) => j !== i))}
                  style={{ background: 'none', border: 'none', color: '#ff4d4d', cursor: 'pointer', fontSize: '0.75rem' }}>✕</button>
              </div>
            ))}
          </div>

          <button className="btn" onClick={generateReport} disabled={!units.length}
            style={{ background: ACCENT, color: '#000', border: 'none', fontWeight: 700 }}>
            Generate Report
          </button>
        </div>

        {/* Report output */}
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <div className="flex justify-between items-center mb-2">
            <h4 style={{ color: ACCENT }}>Report Output</h4>
            {report && <button className="btn btn-outline btn-sm" onClick={exportTxt}>↓ Export TXT</button>}
          </div>
          <textarea value={report} readOnly rows={26}
            placeholder="Report will appear here after generation..."
            style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
              background: '#0e1016', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px',
              color: '#a0a0a0', padding: '0.75rem', resize: 'vertical' }} />
        </div>
      </div>
    </div>
  )
}
