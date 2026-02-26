/**
 * Automation Flow Designer
 * ========================
 * React Flow–based engineering diagramming tool.
 * Replaces the tkinter AutomationDesigner.py with a full canvas-based node editor.
 *
 * Node types mirror the step types from the original PPV AutomationDesigner.
 */
import { useState, useCallback, useRef } from 'react'
import ReactFlow, {
  addEdge,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Panel,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { flowsApi } from '../../services/api'

const ACCENT = '#00c9a7'

// ── Node type definitions ──────────────────────────────────────────────────

const STEP_TYPES = [
  { value: 'set_vid',            label: 'Set VID',              color: '#00d4ff' },
  { value: 'set_ww',             label: 'Set Work Week',        color: '#00d4ff' },
  { value: 'set_bucket',         label: 'Set Bucket',           color: '#00d4ff' },
  { value: 'run_script',         label: 'Run Script',           color: '#00c9a7' },
  { value: 'copy_files',         label: 'Copy Files',           color: '#ffbd2e' },
  { value: 'parse_logs',         label: 'Parse Logs',           color: '#7000ff' },
  { value: 'generate_report',    label: 'Generate Report',      color: '#00ff9d' },
  { value: 'send_notification',  label: 'Send Notification',    color: '#ff9f45' },
  { value: 'conditional_branch', label: 'Conditional Branch',   color: '#ff4d4d' },
  { value: 'custom',             label: 'Custom Step',          color: '#a0a0a0' },
]

const TYPE_MAP = Object.fromEntries(STEP_TYPES.map(t => [t.value, t]))

// ── Custom Node ────────────────────────────────────────────────────────────

import { Handle, Position } from 'reactflow'

function StepNode({ data }) {
  const meta = TYPE_MAP[data.stepType] || TYPE_MAP.custom
  return (
    <div style={{
      background: '#1a1d26',
      border: `1.5px solid ${meta.color}`,
      borderRadius: '8px',
      padding: '10px 14px',
      minWidth: '160px',
      fontFamily: 'Inter, sans-serif',
    }}>
      <Handle type="target" position={Position.Top}
        style={{ background: meta.color, width: 10, height: 10 }} />
      <div style={{ color: meta.color, fontWeight: 700, fontSize: '0.8rem', marginBottom: '4px' }}>
        {meta.label}
      </div>
      <div style={{ color: '#e0e0e0', fontSize: '0.78rem' }}>{data.label || '(unnamed)'}</div>
      {data.params && Object.keys(data.params).length > 0 && (
        <div style={{ marginTop: '6px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '4px' }}>
          {Object.entries(data.params).map(([k, v]) => (
            <div key={k} style={{ fontSize: '0.7rem', color: '#a0a0a0' }}>
              <span style={{ color: '#666' }}>{k}: </span>{String(v)}
            </div>
          ))}
        </div>
      )}
      <Handle type="source" position={Position.Bottom}
        style={{ background: meta.color, width: 10, height: 10 }} />
    </div>
  )
}

const nodeTypes = { stepNode: StepNode }

// ── Edge defaults ─────────────────────────────────────────────────────────

const defaultEdgeOptions = {
  style: { strokeWidth: 2, stroke: '#444' },
  markerEnd: { type: MarkerType.ArrowClosed, color: '#444' },
  animated: false,
}

// ── Main component ─────────────────────────────────────────────────────────

let nodeIdCounter = 1

export default function AutomationDesigner() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedType, setSelectedType] = useState('run_script')
  const [label, setLabel] = useState('')
  const [paramsText, setParamsText] = useState('{}')
  const [flowName, setFlowName] = useState('my_flow')
  const [toast, setToast] = useState(null)
  const reactFlowWrapper = useRef(null)
  const [rfInstance, setRfInstance] = useState(null)

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3000)
  }

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...defaultEdgeOptions, ...params }, eds)),
    [setEdges]
  )

  // ── Add node ─────────────────────────────────────────────────────────────

  const addNode = () => {
    let params = {}
    try { params = JSON.parse(paramsText || '{}') } catch { showToast('Invalid JSON in params', 'error'); return }

    const meta = TYPE_MAP[selectedType] || TYPE_MAP.custom
    const id = `node_${nodeIdCounter++}`
    const newNode = {
      id,
      type: 'stepNode',
      position: { x: 150 + (nodes.length % 4) * 200, y: 80 + Math.floor(nodes.length / 4) * 160 },
      data: {
        stepType: selectedType,
        label: label || meta.label,
        params,
      },
    }
    setNodes((nds) => [...nds, newNode])
    setLabel('')
    setParamsText('{}')
    showToast(`Added: ${label || meta.label}`, 'success')
  }

  // ── Export ────────────────────────────────────────────────────────────────

  const exportJSON = () => {
    const flow = {
      version: '1.0',
      name: flowName,
      nodes: nodes.map(n => ({ id: n.id, stepType: n.data.stepType, label: n.data.label, params: n.data.params, position: n.position })),
      edges: edges.map(e => ({ source: e.source, target: e.target })),
    }
    const blob = new Blob([JSON.stringify(flow, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `${flowName}.json`; a.click()
    URL.revokeObjectURL(url)
    showToast('Flow exported.')
  }

  // ── Import ────────────────────────────────────────────────────────────────

  const handleImport = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      try {
        const flow = JSON.parse(ev.target.result)
        const importedNodes = (flow.nodes || []).map(n => ({
          id: n.id,
          type: 'stepNode',
          position: n.position || { x: 0, y: 0 },
          data: { stepType: n.stepType || 'custom', label: n.label || '', params: n.params || {} },
        }))
        const importedEdges = (flow.edges || []).map((e, i) => ({
          id: `e_${i}`,
          source: e.source,
          target: e.target,
          ...defaultEdgeOptions,
        }))
        setNodes(importedNodes)
        setEdges(importedEdges)
        if (flow.name) setFlowName(flow.name)
        showToast(`Imported: ${importedNodes.length} nodes`, 'success')
      } catch {
        showToast('Import failed — invalid JSON', 'error')
      }
    }
    reader.readAsText(file)
    e.target.value = ''
  }

  // ── Save to backend ───────────────────────────────────────────────────────

  const saveToBackend = async () => {
    try {
      const result = await flowsApi.save(flowName, nodes, edges, { createdBy: 'THRHUB' })
      showToast(`Saved: ${result.id}`, 'success')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const clearAll = () => { setNodes([]); setEdges([]); showToast('Canvas cleared.') }

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 70px)', padding: 0 }}>
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      {/* Header strip */}
      <div style={{
        padding: '0.75rem 1.5rem',
        background: '#15171e',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        flexShrink: 0,
      }}>
        <span style={{ color: ACCENT, fontSize: '1.1rem' }}>⬡</span>
        <span style={{ color: ACCENT, fontWeight: 700 }}>Automation Flow Designer</span>
        <span style={{ color: '#555', fontSize: '0.8rem' }}>React Flow — engineering diagramming</span>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* ── Left panel ────────────────────────────────────────────────── */}
        <div style={{
          width: '280px',
          flexShrink: 0,
          background: '#12141a',
          borderRight: '1px solid rgba(255,255,255,0.07)',
          overflowY: 'auto',
          padding: '1rem',
        }}>
          <h4 style={{ color: ACCENT, marginBottom: '1rem', fontSize: '0.9rem' }}>Add Node</h4>

          <label>Step Type</label>
          <select value={selectedType} onChange={e => setSelectedType(e.target.value)} className="mb-2">
            {STEP_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>

          <label>Label</label>
          <input value={label} onChange={e => setLabel(e.target.value)}
            placeholder="Descriptive name" className="mb-2" />

          <label>Parameters (JSON)</label>
          <textarea value={paramsText} onChange={e => setParamsText(e.target.value)}
            rows={4} placeholder='{"key": "value"}' className="mb-2" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }} />

          <button className="btn btn-outline w-full mb-2" onClick={addNode}>+ Add Node</button>

          <hr className="divider" />

          <label>Flow Name</label>
          <input value={flowName} onChange={e => setFlowName(e.target.value)} className="mb-2" />

          <button className="btn btn-outline w-full mb-2" onClick={exportJSON}>↓ Export JSON</button>
          <button className="btn btn-outline w-full mb-2" onClick={saveToBackend}>💾 Save to Server</button>

          <label style={{ marginTop: '0.5rem' }}>Import JSON</label>
          <label className="upload-zone" style={{ cursor: 'pointer' }}>
            <input type="file" accept=".json" onChange={handleImport} style={{ display: 'none' }} />
            Drop or browse .json
          </label>

          <button className="btn btn-danger w-full mt-4" onClick={clearAll}>✕ Clear Canvas</button>

          <hr className="divider" />
          <div style={{ fontSize: '0.75rem', color: '#555' }}>
            <div>{nodes.length} nodes · {edges.length} edges</div>
            <div style={{ marginTop: '0.3rem' }}>Drag nodes to reposition. Click edges to delete.</div>
          </div>
        </div>

        {/* ── React Flow canvas ──────────────────────────────────────────── */}
        <div ref={reactFlowWrapper} style={{ flex: 1 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
            onInit={setRfInstance}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#1a1d26" gap={20} size={1} />
            <Controls style={{ background: '#15171e', border: '1px solid rgba(255,255,255,0.08)' }} />
            <MiniMap
              nodeColor={(n) => TYPE_MAP[n.data?.stepType]?.color || '#a0a0a0'}
              style={{ background: '#15171e', border: '1px solid rgba(255,255,255,0.08)' }}
            />
            <Panel position="top-right" style={{ background: 'transparent' }}>
              <div style={{ color: '#555', fontSize: '0.72rem', textAlign: 'right' }}>
                Connect nodes by dragging from bottom handles
              </div>
            </Panel>
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}
