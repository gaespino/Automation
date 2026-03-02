import { useState } from 'react';
import { NODE_TYPES_META } from '../nodes/FlowNode';
import './Sidebar.css';

interface SidebarProps {
  nodes: any[];
  edges: any[];
  log: string[];
  experiments: Record<string, unknown>;
  onSelectNode: (id: string) => void;
  onRename: (id: string, name: string) => void;
  onDelete: (id: string) => void;
  onAssign: (id: string, exp: string) => void;
  onAddNode: (nodeType: string) => void;
  onDeleteEdge: (edgeId: string) => void;
}

export default function Sidebar({
  nodes, edges, log, experiments,
  onSelectNode, onRename, onDelete, onAssign, onAddNode, onDeleteEdge,
}: SidebarProps) {
  const [editing, setEditing] = useState<{id:string;name:string;exp:string}|null>(null);

  const openEdit = (n: any) => {
    setEditing({ id: n.id, name: n.data.label, exp: n.data.experiment ?? '' });
  };

  const saveEdit = () => {
    if (!editing) return;
    if (editing.name !== nodes.find(n => n.id === editing.id)?.data.label)
      onRename(editing.id, editing.name);
    if (editing.exp)
      onAssign(editing.id, editing.exp);
    setEditing(null);
  };

  return (
    <div className="ad-sidebar">
      {/* ─── Node Palette ─────────────────────────────────────── */}
      <div className="section-title">Node Palette</div>
      <div className="sb-palette">
        {Object.entries(NODE_TYPES_META).map(([type, meta]) => (
          <button
            key={type}
            className="sb-palette-btn"
            style={{ borderColor: meta.color }}
            title={`Add ${meta.label}`}
            onClick={() => onAddNode(type)}
          >
            <span className="sb-palette-sym" style={{ background: meta.color }}>
              {meta.symbol}
            </span>
            <span className="sb-palette-label">{meta.label}</span>
          </button>
        ))}
      </div>

      {/* ─── Node Editor ──────────────────────────────────────── */}
      <div className="section-title">Node Editor</div>
      {editing ? (
        <div className="sb-editor">
          <label>ID: <span style={{color:'#4ec9b0'}}>{editing.id}</span></label>
          <label>Name</label>
          <input value={editing.name}
            onChange={e => setEditing(s => s ? {...s, name: e.target.value} : s)} />
          <label>Experiment</label>
          <select value={editing.exp}
            onChange={e => setEditing(s => s ? {...s, exp: e.target.value} : s)}>
            <option value="">— none —</option>
            {Object.keys(experiments).map(k => <option key={k} value={k}>{k}</option>)}
          </select>
          <div className="sb-btn-row">
            <button className="btn primary" onClick={saveEdit}>Apply</button>
            <button className="btn" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </div>
      ) : (
        <div className="dim" style={{marginBottom:8}}>Click ✏ on a node to edit.</div>
      )}

      {/* ─── Flow Nodes ───────────────────────────────────────── */}
      <div className="section-title">Flow Nodes ({nodes.length})</div>
      <div className="sb-node-list">
        {nodes.length === 0
          ? <div className="dim">No nodes yet.</div>
          : nodes.map(n => {
            const meta = NODE_TYPES_META[n.data.nodeType];
            return (
              <div key={n.id} className="sb-node-row" onClick={() => onSelectNode(n.id)}>
                <span className="sb-node-dot" style={{background: meta?.color ?? '#555'}}>
                  {meta?.symbol ?? '?'}
                </span>
                <span className="sb-node-name">{n.data.label}</span>
                <span className="sb-node-exp">{n.data.experiment ?? ''}</span>
                <button className="sb-btn" title="Edit" onClick={e => { e.stopPropagation(); openEdit(n); }}>✏</button>
                <button className="sb-btn danger" title="Delete"
                  onClick={e => { e.stopPropagation(); onDelete(n.id); setEditing(null); }}>✕</button>
              </div>
            );
          })}
      </div>

      {/* ─── Connections ──────────────────────────────────────── */}
      <div className="section-title">Connections ({edges.length})</div>
      <div className="sb-edge-list">
        {edges.map(e => (
          <div key={e.id} className="sb-edge-row">
            <span style={{color: e.style?.stroke ?? '#858585'}}>{e.label}</span>
            <span className="sb-edge-path">{e.source} → {e.target}</span>
            <button
              className="sb-btn danger"
              title="Remove connection"
              onClick={() => onDeleteEdge(e.id)}
            >✕</button>
          </div>
        ))}
      </div>

      {/* ─── Log ──────────────────────────────────────────────── */}
      <div className="section-title">Log</div>
      <div className="log-area sb-log">
        {log.join('\n')}
      </div>
    </div>
  );
}
