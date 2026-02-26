/**
 * File Handler
 * ============
 * Merge and manage multiple data files (DPMB format, MCA reports).
 */
import { useState } from 'react'

const ACCENT = '#ffbd2e'

export default function FileHandler() {
  const [files, setFiles] = useState([])
  const [merged, setMerged] = useState('')
  const [mode, setMode] = useState('merge')

  const addFiles = (e) => {
    const newFiles = Array.from(e.target.files)
    const readers = newFiles.map(f => new Promise(res => {
      const r = new FileReader()
      r.onload = ev => res({ name: f.name, content: ev.target.result, size: f.size })
      r.readAsText(f)
    }))
    Promise.all(readers).then(loaded => setFiles(prev => [...prev, ...loaded]))
    e.target.value = ''
  }

  const mergeFiles = () => {
    if (!files.length) return
    const separator = mode === 'append' ? '\n\n' : '\n'
    const result = files.map(f => `# === ${f.name} ===\n${f.content}`).join(separator)
    setMerged(result)
  }

  const exportMerged = () => {
    if (!merged) return
    const blob = new Blob([merged], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'merged_output.txt'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title" style={{ color: ACCENT }}>📁 File Handler</h1>
        <p className="page-subtitle">Merge and manage multiple data files — DPMB format, MCA reports, batch file operations</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1rem' }}>
        {/* Controls */}
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <h4 style={{ color: ACCENT, marginBottom: '1rem' }}>File Operations</h4>

          <label>Merge Mode</label>
          <select value={mode} onChange={e => setMode(e.target.value)} className="mb-3">
            <option value="merge">Merge (concatenate)</option>
            <option value="append">Append with separators</option>
          </select>

          <label className="btn btn-outline w-full mb-3" style={{ cursor: 'pointer', textAlign: 'center', justifyContent: 'center' }}>
            + Add Files
            <input type="file" multiple onChange={addFiles} style={{ display: 'none' }} />
          </label>

          <div className="mb-4" style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {files.length === 0 ? (
              <p className="text-muted" style={{ fontSize: '0.82rem', textAlign: 'center', padding: '1rem' }}>
                No files loaded
              </p>
            ) : files.map((f, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '0.4rem 0.6rem', borderBottom: '1px solid rgba(255,255,255,0.05)',
                fontSize: '0.8rem',
              }}>
                <div>
                  <div style={{ color: '#e0e0e0' }}>{f.name}</div>
                  <div style={{ color: '#555', fontSize: '0.72rem' }}>{(f.size / 1024).toFixed(1)} KB</div>
                </div>
                <button onClick={() => setFiles(fs => fs.filter((_, j) => j !== i))}
                  style={{ background: 'none', border: 'none', color: '#ff4d4d', cursor: 'pointer' }}>✕</button>
              </div>
            ))}
          </div>

          <button className="btn w-full mb-2" onClick={mergeFiles} disabled={!files.length}
            style={{ background: ACCENT, color: '#000', border: 'none', fontWeight: 700 }}>
            Merge Files ({files.length})
          </button>
          <button className="btn btn-outline w-full mb-2" onClick={exportMerged} disabled={!merged}>
            ↓ Export Merged
          </button>
          <button className="btn btn-danger w-full" onClick={() => { setFiles([]); setMerged('') }}>
            Clear All
          </button>
        </div>

        {/* Preview */}
        <div className="card" style={{ borderLeft: `3px solid ${ACCENT}` }}>
          <div className="flex justify-between items-center mb-2">
            <h4 style={{ color: ACCENT }}>Merged Preview</h4>
            {merged && <span className="badge badge-info">{merged.split('\n').length} lines</span>}
          </div>
          <textarea value={merged} readOnly
            rows={24}
            style={{ width: '100%', fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
              background: '#0e1016', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px',
              color: '#a0a0a0', padding: '0.75rem', resize: 'vertical' }}
            placeholder="Merged output will appear here..." />
        </div>
      </div>
    </div>
  )
}
