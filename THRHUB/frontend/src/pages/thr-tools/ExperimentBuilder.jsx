/**
 * Experiment Builder
 * ==================
 * Excel-notebook–style tool for building multi-experiment JSON configs.
 * Each "tab" = one experiment (mimicking the tkinter tab-per-experiment design).
 * Per-product field enable/disable from GNR/CWF/DMR ControlPanelConfig.json.
 *
 * Replaces ExperimentBuilder.py (tkinter) with a React implementation.
 */
import { useState, useEffect } from 'react'
import { configApi, experimentsApi } from '../../services/api'

const ACCENT = '#36d7b7'
const PRODUCTS = ['GNR', 'CWF', 'DMR']
const ENVIRONMENTS = ['SLT', 'CHx', 'SORT', 'CLASS', 'FINAL']

// ── Helpers ───────────────────────────────────────────────────────────────

function emptyExperiment(product = 'GNR', idx = 1) {
  return {
    _id: `exp_${Date.now()}_${idx}`,
    name: `Experiment_${idx}`,
    product,
    environment: 'SLT',
    // Basic
    Experiment: '',
    'Test Name': '',
    'Test Mode': 'Mesh',
    'Test Type': 'Loops',
    // Unit data
    'Visual ID': '',
    Bucket: '',
    'COM Port': '',
    'IP Address': '',
    // Advanced
    'TTL Folder': '',
    'Scripts File': '',
    'Pass String': '',
    'Fail String': '',
    'Post Process': '',
    // Loops
    Loops: '1',
    // Voltage
    'Voltage Type': 'vbump',
    'Voltage IA': '',
    'Voltage CFC': '',
    'Frequency IA': '',
    'Frequency CFC': '',
    // Notes
    Notes: '',
  }
}

// ── Field component ───────────────────────────────────────────────────────

function Field({ label, fieldKey, value, onChange, disabled, options, type = 'text' }) {
  const baseStyle = {
    width: '100%',
    background: disabled ? 'rgba(255,255,255,0.02)' : '#1a1d26',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '5px',
    color: disabled ? '#444' : '#e0e0e0',
    padding: '0.35rem 0.6rem',
    fontSize: '0.83rem',
    fontFamily: 'var(--font-ui)',
    cursor: disabled ? 'not-allowed' : 'auto',
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.45rem' }}>
      <label style={{ width: '160px', flexShrink: 0, fontSize: '0.78rem', color: disabled ? '#444' : '#a0a0a0' }}>
        {label}
      </label>
      {options ? (
        <select value={value || ''} onChange={e => onChange(fieldKey, e.target.value)}
          disabled={disabled} style={baseStyle}>
          {options.map(o => <option key={o} value={o}>{o || '—'}</option>)}
        </select>
      ) : type === 'checkbox' ? (
        <input type="checkbox" checked={Boolean(value)}
          onChange={e => onChange(fieldKey, e.target.checked)}
          disabled={disabled} style={{ accentColor: ACCENT }} />
      ) : (
        <input type="text" value={value || ''} onChange={e => onChange(fieldKey, e.target.value)}
          disabled={disabled} style={baseStyle} />
      )}
    </div>
  )
}

// ── Section ───────────────────────────────────────────────────────────────

function Section({ title, children }) {
  const [open, setOpen] = useState(true)
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <div
        onClick={() => setOpen(o => !o)}
        style={{
          background: 'rgba(255,255,255,0.04)', borderRadius: '5px',
          padding: '0.4rem 0.75rem', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          userSelect: 'none', marginBottom: '0.5rem',
        }}
      >
        <span style={{ color: ACCENT, fontSize: '0.82rem', fontWeight: 600 }}>{title}</span>
        <span style={{ color: '#555', fontSize: '0.75rem' }}>{open ? '▲' : '▼'}</span>
      </div>
      {open && <div style={{ paddingLeft: '0.25rem' }}>{children}</div>}
    </div>
  )
}

// ── Experiment tab panel ──────────────────────────────────────────────────

function ExperimentPanel({ exp, cfg, onChange }) {
  const fieldConfigs = cfg?.field_configs || {}

  const isDisabled = (key) => {
    const fc = fieldConfigs[key]
    if (!fc) return false
    // product-level enable check
    const enableCfg = cfg?.field_enable_config || {}
    for (const [fk, products] of Object.entries(enableCfg)) {
      if (fk === key && !products.includes(exp.product)) return true
    }
    return false
  }

  const optionsFor = (key) => fieldConfigs[key]?.options

  const update = (key, val) => onChange({ ...exp, [key]: val })

  return (
    <div style={{ overflowY: 'auto', padding: '0.75rem', maxHeight: 'calc(100vh - 240px)' }}>
      <Section title="Basic Information">
        <Field label="Experiment" fieldKey="Experiment" value={exp.Experiment} onChange={update} disabled={isDisabled('Experiment')} />
        <Field label="Test Name"  fieldKey="Test Name"  value={exp['Test Name']}  onChange={update} disabled={isDisabled('Test Name')} />
        <Field label="Test Mode"  fieldKey="Test Mode"  value={exp['Test Mode']}  onChange={update} options={optionsFor('Test Mode')  || ['Mesh','Slice']} />
        <Field label="Test Type"  fieldKey="Test Type"  value={exp['Test Type']}  onChange={update} options={optionsFor('Test Type')  || ['Loops','Sweep','Shmoo']} />
        <Field label="Content"    fieldKey="Content"    value={exp.Content}        onChange={update} options={['Linux','Dragon','PYSVConsole']} />
      </Section>

      <Section title="Unit Data">
        <Field label="Visual ID"  fieldKey="Visual ID"  value={exp['Visual ID']}  onChange={update} />
        <Field label="Bucket"     fieldKey="Bucket"     value={exp.Bucket}         onChange={update} />
        <Field label="COM Port"   fieldKey="COM Port"   value={exp['COM Port']}   onChange={update} disabled={isDisabled('COM Port')} />
        <Field label="IP Address" fieldKey="IP Address" value={exp['IP Address']} onChange={update} />
      </Section>

      <Section title="Voltage & Frequency">
        <Field label="Voltage Type" fieldKey="Voltage Type" value={exp['Voltage Type']} onChange={update}
          options={optionsFor('Voltage Type') || ['vbump','fixed','ppvc']} disabled={isDisabled('Voltage Type')} />
        <Field label="Voltage IA"   fieldKey="Voltage IA"   value={exp['Voltage IA']}   onChange={update} disabled={isDisabled('Voltage IA')} />
        <Field label="Voltage CFC"  fieldKey="Voltage CFC"  value={exp['Voltage CFC']}  onChange={update} disabled={isDisabled('Voltage CFC')} />
        <Field label="Frequency IA" fieldKey="Frequency IA" value={exp['Frequency IA']} onChange={update} disabled={isDisabled('Frequency IA')} />
        <Field label="Frequency CFC"fieldKey="Frequency CFC"value={exp['Frequency CFC']}onChange={update} disabled={isDisabled('Frequency CFC')} />
      </Section>

      {exp['Test Type'] === 'Loops' && (
        <Section title="Loops">
          <Field label="Loops" fieldKey="Loops" value={exp.Loops} onChange={update} />
        </Section>
      )}

      {exp['Test Type'] === 'Sweep' && (
        <Section title="Sweep">
          <Field label="Type"   fieldKey="Sweep Type"   value={exp['Sweep Type']}   onChange={update} options={['Voltage','Frequency']} />
          <Field label="Domain" fieldKey="Domain" value={exp.Domain} onChange={update} options={['IA','CFC']} />
          <Field label="Start"  fieldKey="Start"  value={exp.Start}  onChange={update} />
          <Field label="End"    fieldKey="End"    value={exp.End}    onChange={update} />
          <Field label="Steps"  fieldKey="Steps"  value={exp.Steps}  onChange={update} />
        </Section>
      )}

      <Section title="Advanced Configuration">
        <Field label="TTL Folder"   fieldKey="TTL Folder"   value={exp['TTL Folder']}   onChange={update} />
        <Field label="Scripts File" fieldKey="Scripts File" value={exp['Scripts File']} onChange={update} />
        <Field label="Pass String"  fieldKey="Pass String"  value={exp['Pass String']}  onChange={update} />
        <Field label="Fail String"  fieldKey="Fail String"  value={exp['Fail String']}  onChange={update} />
        <Field label="Post Process" fieldKey="Post Process" value={exp['Post Process']} onChange={update} disabled={isDisabled('Post Process')} />
        <Field label="Fuse File"    fieldKey="Fuse File"    value={exp['Fuse File']}    onChange={update} />
        <Field label="Bios File"    fieldKey="Bios File"    value={exp['Bios File']}    onChange={update} />
      </Section>

      {exp.product === 'GNR' && (
        <Section title="GNR — Core Configuration">
          <Field label="Core License"  fieldKey="Core License"  value={exp['Core License']}  onChange={update}
            options={['','1: SSE/128','2: AVX2/256 Light','3: AVX2/256 Heavy','4: AVX3/512 Light','5: AVX3/512 Heavy','6: TMUL Light','7: TMUL Heavy']} />
          <Field label="600W Unit"     fieldKey="600W Unit"     value={exp['600W Unit']}     onChange={update} type="checkbox" />
          <Field label="Pseudo Config" fieldKey="Pseudo Config" value={exp['Pseudo Config']} onChange={update} type="checkbox" />
        </Section>
      )}

      {exp.product === 'CWF' && (
        <Section title="CWF — Core Configuration">
          <Field label="Disable 2 Cores" fieldKey="Disable 2 Cores" value={exp['Disable 2 Cores']} onChange={update}
            options={['','0x3','0xc','0x9','0xa','0x5']} />
        </Section>
      )}

      {exp.product === 'DMR' && (
        <Section title="DMR — Core Configuration">
          <Field label="Core License" fieldKey="Core License" value={exp['Core License']} onChange={update}
            options={['','1: SSE/128','2: AVX2/256 Light','3: AVX2/256 Heavy']} />
          <Field label="Disable 1 Core" fieldKey="Disable 1 Core" value={exp['Disable 1 Core']} onChange={update}
            options={['','0x1','0x2']} />
        </Section>
      )}

      <Section title="Notes">
        <textarea value={exp.Notes || ''} onChange={e => update('Notes', e.target.value)}
          rows={3} style={{ width: '100%', fontFamily: 'var(--font-ui)', fontSize: '0.83rem',
          background: '#1a1d26', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '5px',
          color: '#e0e0e0', padding: '0.4rem 0.6rem', resize: 'vertical' }} />
      </Section>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────

export default function ExperimentBuilder() {
  const [experiments, setExperiments] = useState([emptyExperiment('GNR', 1)])
  const [activeIdx, setActiveIdx] = useState(0)
  const [globalProduct, setGlobalProduct] = useState('GNR')
  const [cfg, setCfg] = useState({})
  const [sessionName, setSessionName] = useState('')
  const [toast, setToast] = useState(null)

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  // Load product config when product changes
  useEffect(() => {
    configApi.getProductConfig(globalProduct)
      .then(setCfg)
      .catch(() => setCfg({}))
  }, [globalProduct])

  const addTab = () => {
    const newExp = emptyExperiment(globalProduct, experiments.length + 1)
    setExperiments(e => [...e, newExp])
    setActiveIdx(experiments.length)
  }

  const removeTab = (idx) => {
    if (experiments.length === 1) { showToast('Must have at least one experiment.', 'error'); return }
    setExperiments(e => e.filter((_, i) => i !== idx))
    setActiveIdx(i => Math.min(i, experiments.length - 2))
  }

  const updateExperiment = (idx, updated) => {
    setExperiments(e => e.map((x, i) => i === idx ? updated : x))
  }

  const exportJSON = () => {
    const payload = experiments.map(({ _id, ...rest }) => rest)  // eslint-disable-line no-unused-vars
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'experiments.json'; a.click()
    URL.revokeObjectURL(url)
    showToast(`Exported ${payload.length} experiment(s).`, 'success')
  }

  const handleImport = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        let imported = JSON.parse(ev.target.result)
        if (!Array.isArray(imported)) imported = [imported]
        setExperiments(imported.map((x, i) => ({ ...emptyExperiment(x.product || 'GNR', i + 1), ...x, _id: `exp_${Date.now()}_${i}` })))
        setActiveIdx(0)
        showToast(`Imported ${imported.length} experiment(s).`, 'success')
      } catch {
        showToast('Import failed — invalid JSON', 'error')
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  const saveToBackend = async () => {
    const name = sessionName || `session_${new Date().toISOString().slice(0,19)}`
    try {
      const r = await experimentsApi.save(name, experiments.map(({ _id, ...rest }) => rest))  // eslint-disable-line no-unused-vars
      showToast(`Saved session: ${r.id}`, 'success')
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const active = experiments[activeIdx] || experiments[0]

  return (
    <div className="page-container" style={{ padding: 0, height: 'calc(100vh - 70px)', display: 'flex', flexDirection: 'column' }}>
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      {/* Header */}
      <div style={{
        padding: '0.6rem 1.2rem',
        background: '#15171e',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        display: 'flex', alignItems: 'center', gap: '1rem', flexShrink: 0, flexWrap: 'wrap',
      }}>
        <span style={{ color: ACCENT, fontWeight: 700 }}>🧪 Experiment Builder</span>

        <label style={{ marginBottom: 0, color: '#a0a0a0', fontSize: '0.78rem' }}>Product:</label>
        <select value={globalProduct} onChange={e => setGlobalProduct(e.target.value)}
          style={{ background: '#1a1d26', border: '1px solid rgba(255,255,255,0.1)', color: '#e0e0e0',
            borderRadius: '5px', padding: '0.25rem 0.5rem', fontSize: '0.82rem', width: 'auto' }}>
          {PRODUCTS.map(p => <option key={p}>{p}</option>)}
        </select>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input value={sessionName} onChange={e => setSessionName(e.target.value)}
            placeholder="Session name (optional)"
            style={{ background: '#1a1d26', border: '1px solid rgba(255,255,255,0.08)', color: '#e0e0e0',
              borderRadius: '5px', padding: '0.25rem 0.6rem', fontSize: '0.8rem', width: '190px' }} />
          <button className="btn btn-outline btn-sm" onClick={saveToBackend}>💾 Save</button>
          <button className="btn btn-outline btn-sm" onClick={exportJSON}>↓ Export JSON</button>
          <label className="btn btn-outline btn-sm" style={{ cursor: 'pointer', marginBottom: 0 }}>
            ↑ Import
            <input type="file" accept=".json" onChange={handleImport} style={{ display: 'none' }} />
          </label>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0', overflowX: 'auto',
        background: '#12141a', borderBottom: '1px solid rgba(255,255,255,0.07)',
        padding: '0 0.5rem', flexShrink: 0,
      }}>
        {experiments.map((exp, idx) => (
          <div
            key={exp._id}
            onClick={() => setActiveIdx(idx)}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.4rem',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              borderBottom: idx === activeIdx ? `2px solid ${ACCENT}` : '2px solid transparent',
              color: idx === activeIdx ? ACCENT : '#a0a0a0',
              fontSize: '0.82rem', whiteSpace: 'nowrap',
              transition: 'color 0.15s',
            }}
          >
            <span>{exp.name || `Exp ${idx + 1}`}</span>
            <span style={{ color: '#555', fontSize: '0.7rem' }}>[{exp.product}]</span>
            <button
              onClick={e => { e.stopPropagation(); removeTab(idx) }}
              style={{ background: 'none', border: 'none', color: '#555', cursor: 'pointer',
                fontSize: '0.75rem', padding: '0 0.1rem', lineHeight: 1 }}
            >✕</button>
          </div>
        ))}
        <button className="btn btn-sm" onClick={addTab}
          style={{ marginLeft: '0.5rem', color: ACCENT, background: 'none', border: `1px solid ${ACCENT}`,
            borderRadius: '4px', padding: '0.25rem 0.6rem', fontSize: '0.78rem', cursor: 'pointer' }}>
          + Add
        </button>
      </div>

      {/* Content: left = form, right = JSON preview */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Form panel */}
        <div style={{ width: '420px', flexShrink: 0, borderRight: '1px solid rgba(255,255,255,0.07)', background: '#0e1016' }}>
          {/* Tab name + product */}
          <div style={{ padding: '0.6rem 0.75rem', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <input value={active.name} onChange={e => updateExperiment(activeIdx, { ...active, name: e.target.value })}
              style={{ background: 'transparent', border: 'none', color: ACCENT, fontWeight: 600,
                fontSize: '0.9rem', flex: 1, outline: 'none' }} />
            <select value={active.product} onChange={e => updateExperiment(activeIdx, { ...active, product: e.target.value })}
              style={{ background: '#1a1d26', border: '1px solid rgba(255,255,255,0.08)', color: '#e0e0e0',
                borderRadius: '5px', padding: '0.2rem 0.4rem', fontSize: '0.78rem', width: 'auto' }}>
              {PRODUCTS.map(p => <option key={p}>{p}</option>)}
            </select>
            <select value={active.environment} onChange={e => updateExperiment(activeIdx, { ...active, environment: e.target.value })}
              style={{ background: '#1a1d26', border: '1px solid rgba(255,255,255,0.08)', color: '#e0e0e0',
                borderRadius: '5px', padding: '0.2rem 0.4rem', fontSize: '0.78rem', width: 'auto' }}>
              {ENVIRONMENTS.map(ev => <option key={ev}>{ev}</option>)}
            </select>
          </div>
          <ExperimentPanel exp={active} cfg={cfg} onChange={(updated) => updateExperiment(activeIdx, updated)} />
        </div>

        {/* JSON preview */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
            <span style={{ color: ACCENT, fontWeight: 600, fontSize: '0.85rem' }}>
              JSON Preview — All {experiments.length} experiment(s)
            </span>
          </div>
          <pre style={{
            background: '#0e1016', border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '8px', padding: '1rem', color: '#a0a0a0',
            fontSize: '0.75rem', fontFamily: 'var(--font-mono)',
            whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: 0,
          }}>
            {JSON.stringify(experiments.map(({ _id, ...r }) => r), null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}
