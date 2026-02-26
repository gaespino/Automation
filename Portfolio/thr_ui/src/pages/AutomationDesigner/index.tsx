import React, { useCallback, useRef, useState } from 'react';
import {
  ReactFlow, Background, Controls, MiniMap,
  addEdge, useNodesState, useEdgesState,
  BackgroundVariant, type Connection, type NodeTypes,
  Panel, MarkerType, type Node, type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './AutomationDesigner.css';
import FlowNode, { NODE_TYPES_META, type FlowNodeData, type FlowNodeType } from './nodes/FlowNode';
import Sidebar from './sidebar/Sidebar';
import { api } from '../../api/client';
import toast, { Toaster } from 'react-hot-toast';

// Register custom node type
const nodeTypes: NodeTypes = {
  flowNode: FlowNode as any,
};

let _nodeCounter = 0;
function newId() { return `NODE_${String(++_nodeCounter).padStart(3,'0')}`; }

const PORT_COLORS: Record<string, string> = {
  p0: '#4ec9b0', p1: '#f44747', p2: '#ce9178', p3: '#9b9bff',
};

export default function AutomationDesigner() {
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [experiments, setExperiments] = useState<Record<string, unknown>>({});
  const [unitConfig, setUnitConfig] = useState({
    product: 'GNR', visual_id: '', bucket: '', com_port: '', ip: '',
    flag_600w: false, check_core: 5,
  });
  const [log, setLog] = useState<string[]>(['Automation Designer ready.']);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] = useState<any>(null);

  const addLog = (msg: string) => {
    const ts = new Date().toLocaleTimeString();
    setLog(l => [`[${ts}] ${msg}`, ...l].slice(0, 200));
  };

  // ── Add node ──────────────────────────────────────────────────────────────
  const addNode = useCallback((nodeType: string) => {
    const meta = NODE_TYPES_META[nodeType];
    if (!meta) return;
    const id = newId();
    const n = nodes.length;
    const x = Math.round((160 + (n % 4) * 220) / 20) * 20;
    const y = Math.round((160 + Math.floor(n / 4) * 180) / 20) * 20;
    setNodes(ns => [...ns, {
      id,
      type: 'flowNode',
      position: { x, y },
      data: { label: id, nodeType, experiment: undefined },
    }]);
    addLog(`Added ${meta.label}: ${id}`);
  }, [nodes, setNodes]);

  // ── Connect ───────────────────────────────────────────────────────────────
  const onConnect = useCallback((params: Connection) => {
    // Enforce port uniqueness: one wire per source handle
    const duplicate = edges.find(e => e.source === params.source && e.sourceHandle === params.sourceHandle);
    if (duplicate) {
      toast.error(`Port ${params.sourceHandle} on ${params.source} is already connected. Delete it first.`);
      return;
    }
    const portNum = parseInt((params.sourceHandle ?? 'p0').replace('p',''));
    const portColor = PORT_COLORS[params.sourceHandle ?? 'p0'] ?? '#858585';
    setEdges(es => addEdge({
      ...params,
      type: 'smoothstep',
      animated: false,
      label: `P${portNum}`,
      style: { stroke: portColor, strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: portColor },
    }, es));
    addLog(`Connected ${params.source}:${params.sourceHandle} → ${params.target}`);
  }, [edges, setEdges]);

  // ── Delete selected ───────────────────────────────────────────────────────
  const deleteSelected = useCallback(() => {
    const selNodes = nodes.filter(n => n.selected);
    const selEdges = edges.filter(e => e.selected);
    if (selNodes.length === 0 && selEdges.length === 0) {
      toast('Select a node or edge first (click to select).'); return;
    }
    const delIds = new Set(selNodes.map(n => n.id));
    setNodes(ns => ns.filter(n => !n.selected));
    setEdges(es => es.filter(e => !e.selected && !delIds.has(e.source) && !delIds.has(e.target)));
    addLog(`Deleted ${selNodes.length} node(s), ${selEdges.length} edge(s).`);
  }, [nodes, edges, setNodes, setEdges]);

  // ── Auto layout ───────────────────────────────────────────────────────────
  const autoLayout = useCallback(async () => {
    const flowData = buildFlowPayload(nodes, edges, unitConfig, experiments);
    try {
      const resp = await api.post('/flow/layout', flowData);
      const positions: Record<string, {x:number;y:number}> = resp.data.positions;
      setNodes(ns => ns.map(n => positions[n.id]
        ? { ...n, position: positions[n.id] } : n));
      addLog('Auto layout applied.');
    } catch {
      toast.error('Layout failed — see console.');
    }
  }, [nodes, edges, unitConfig, experiments, setNodes]);

  // ── Validate ──────────────────────────────────────────────────────────────
  const validate = useCallback(async () => {
    const flowData = buildFlowPayload(nodes, edges, unitConfig, experiments);
    try {
      const resp = await api.post('/flow/validate', flowData);
      const { valid, errors, warnings } = resp.data;
      if (valid && warnings.length === 0) {
        toast.success('Flow is valid ✓');
      } else if (errors.length) {
        errors.forEach((e: string) => toast.error(e));
      } else {
        warnings.forEach((w: string) => toast(w, { icon: '⚠️' }));
      }
    } catch { toast.error('Validation error'); }
  }, [nodes, edges, unitConfig, experiments]);

  // ── Save ──────────────────────────────────────────────────────────────────
  const saveFlow = useCallback(() => {
    const data = { ...buildFlowPayload(nodes, edges, unitConfig, experiments), _format: 'web' };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(blob), download: 'flow_design.json',
    });
    a.click(); URL.revokeObjectURL(a.href);
    addLog('Flow saved.');
    toast.success('Flow saved.');
  }, [nodes, edges, unitConfig, experiments]);

  // ── Load ──────────────────────────────────────────────────────────────────
  const loadFlow = useCallback((flowJson: unknown) => {
    const raw = flowJson as any;
    const isWeb = raw._format === 'web';
    const newNodes = Object.values(raw.nodes ?? {}).map((n: any) => ({
      id: n.id,
      type: 'flowNode',
      position: {
        x: isWeb ? n.x : n.x + 75,
        y: isWeb ? n.y : n.y + 50,
      },
      data: { label: n.name, nodeType: n.type, experiment: n.experiment ?? undefined },
    }));
    const newEdges: any[] = [];
    for (const n of Object.values(raw.nodes ?? {}) as any[]) {
      for (const [port, target] of Object.entries(n.connections ?? {})) {
        const portNum = parseInt(port);
        const portColor = PORT_COLORS[`p${portNum}`] ?? '#858585';
        newEdges.push({
          id: `${n.id}-p${portNum}-${target}`,
          source: n.id, target: target as string,
          sourceHandle: `p${portNum}`, targetHandle: 'in',
          type: 'smoothstep',
          label: `P${portNum}`,
          style: { stroke: portColor, strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: portColor },
        });
      }
    }
    _nodeCounter = newNodes.length;
    setNodes(newNodes as any);
    setEdges(newEdges);
    if (raw.experiments) setExperiments(raw.experiments);
    addLog(`Loaded flow: ${newNodes.length} nodes, ${newEdges.length} edges.`);
    toast.success('Flow loaded.');
  }, [setNodes, setEdges]);

  // ── Export ZIP ────────────────────────────────────────────────────────────
  const exportZip = useCallback(async () => {
    const flowData = buildFlowPayload(nodes, edges, unitConfig, experiments);
    try {
      const resp = await api.post('/flow/export', flowData, { responseType: 'blob' });
      const a = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(resp.data), download: 'FlowConfig.zip',
      });
      a.click(); URL.revokeObjectURL(a.href);
      addLog('Exported ZIP.'); toast.success('ZIP exported.');
    } catch { toast.error('Export failed'); }
  }, [nodes, edges, unitConfig, experiments]);

  // ── Node click → update experiment ───────────────────────────────────────
  const onNodeDoubleClick = useCallback((_: React.MouseEvent, node: any) => {
    const exp = prompt(`Assign experiment to ${node.id} (${node.data.label}):`, node.data.experiment ?? '');
    if (exp !== null) {
      setNodes(ns => ns.map(n => n.id === node.id
        ? { ...n, data: { ...n.data, experiment: exp || undefined } } : n));
      addLog(`${node.id} → experiment: "${exp}"`);
    }
  }, [setNodes]);

  // ── Context menu (right-click) ────────────────────────────────────────────
  const [ctxMenu, setCtxMenu] = useState<{x:number;y:number;nodeId:string}|null>(null);
  const onNodeContextMenu = useCallback((e: React.MouseEvent, node: any) => {
    e.preventDefault();
    setCtxMenu({ x: e.clientX, y: e.clientY, nodeId: node.id });
  }, []);
  const closeCtx = () => setCtxMenu(null);

  const ctxRename = () => {
    if (!ctxMenu) return;
    const n = nodes.find(n => n.id === ctxMenu.nodeId);
    const name = prompt(`Rename node (${ctxMenu.nodeId}):`, n?.data.label ?? ctxMenu.nodeId);
    if (name) {
      setNodes(ns => ns.map(nd => nd.id === ctxMenu.nodeId
        ? { ...nd, data: { ...nd.data, label: name } } : nd));
    }
    closeCtx();
  };

  const ctxDelete = () => {
    if (!ctxMenu) return;
    setNodes(ns => ns.filter(n => n.id !== ctxMenu.nodeId));
    setEdges(es => es.filter(e => e.source !== ctxMenu.nodeId && e.target !== ctxMenu.nodeId));
    addLog(`Deleted node ${ctxMenu.nodeId}.`);
    closeCtx();
  };

  const ctxAssignExp = () => {
    if (!ctxMenu) return;
    const keys = Object.keys(experiments);
    const list = keys.length ? keys.join('\n') : '(no experiments loaded)';
    const exp = prompt(`Assign experiment to ${ctxMenu.nodeId}:\nAvailable:\n${list}`, '');
    if (exp && keys.includes(exp)) {
      setNodes(ns => ns.map(nd => nd.id === ctxMenu.nodeId
        ? { ...nd, data: { ...nd.data, experiment: exp } } : nd));
      addLog(`${ctxMenu.nodeId} → experiment: "${exp}"`);
    } else if (exp) toast.error(`Experiment "${exp}" not found`);
    closeCtx();
  };

  return (
    <div className="ad-root" onClick={closeCtx}>
      <Toaster position="top-right" toastOptions={{ style: { background:'#252526', color:'#d4d4d4', border:'1px solid #3e3e42', fontSize:'12px' } }} />

      {/* Toolbar */}
      <div className="ad-toolbar">
        <span className="ad-title">Automation Designer</span>
        <div className="ad-tool-group">
          {Object.entries(NODE_TYPES_META).map(([type, meta]) => (
            <button key={type} className="btn ad-palette-btn"
              style={{ borderColor: meta.color, color: meta.color }}
              title={`Add ${meta.label}`}
              onClick={e => { e.stopPropagation(); addNode(type); }}>
              {meta.symbol}
            </button>
          ))}
        </div>
        <div className="ad-tool-sep" />
        <button className="btn danger" onClick={deleteSelected}>✕ Delete</button>
        <button className="btn" onClick={autoLayout}>⟲ Layout</button>
        <button className="btn" onClick={validate}>✓ Validate</button>
        <div className="ad-tool-sep" />
        <button className="btn primary" onClick={saveFlow}>💾 Save</button>
        <label className="btn" title="Load flow JSON">
          📂 Load
          <input type="file" accept=".json" style={{display:'none'}}
            onChange={e => {
              const f = e.target.files?.[0];
              if (!f) return;
              const r = new FileReader();
              r.onload = ev => {
                try { loadFlow(JSON.parse(ev.target!.result as string)); }
                catch { toast.error('Invalid JSON'); }
              };
              r.readAsText(f);
              e.target.value = '';
            }} />
        </label>
        <button className="btn" onClick={exportZip}>⬇ Export ZIP</button>
      </div>

      {/* Main area */}
      <div className="ad-main">
        {/* Left sidebar — Unit Config */}
        <div className="ad-left">
          <div className="section-title">Product</div>
          <select value={unitConfig.product}
            onChange={e => setUnitConfig(u => ({...u, product: e.target.value}))}
            style={{width:'100%', marginBottom:10}}>
            {['GNR','CWF','DMR','SRF'].map(p => <option key={p}>{p}</option>)}
          </select>

          <div className="section-title">Unit Config</div>
          {([
            ['visual_id',  'Visual ID'],
            ['bucket',     'Bucket'],
            ['com_port',   'COM Port'],
            ['ip',         'IP Address'],
          ] as [keyof typeof unitConfig, string][]).map(([key, label]) => (
            <div key={key} className="ad-field">
              <label>{label}</label>
              <input value={unitConfig[key] as string}
                onChange={e => setUnitConfig(u => ({...u, [key]: e.target.value}))} />
            </div>
          ))}
          <div className="ad-field">
            <label>Check Core</label>
            <input type="number" step={1} value={unitConfig.check_core}
              onChange={e => setUnitConfig(u => ({...u, check_core: parseInt(e.target.value)||0}))} />
          </div>
          <div className="ad-field row">
            <label><input type="checkbox" checked={unitConfig.flag_600w}
              onChange={e => setUnitConfig(u=>({...u,flag_600w:e.target.checked}))} /> 600W Unit</label>
          </div>

          <div className="section-title" style={{marginTop:12}}>Load Experiments</div>
          <label className="btn" style={{display:'block',textAlign:'center',cursor:'pointer'}}>
            📂 Browse (.json/.tpl/.xlsx)
            <input type="file" accept=".json,.tpl,.xlsx" style={{display:'none'}}
              onChange={e => {
                const f = e.target.files?.[0];
                if (!f) return;
                const r = new FileReader();
                r.onload = ev => {
                  try {
                    const parsed = JSON.parse(ev.target!.result as string);
                    const exps: Record<string,unknown> = Array.isArray(parsed)
                      ? Object.fromEntries(parsed.map((x:any) => [x.ExperimentName ?? x.name ?? 'Exp', x]))
                      : parsed;
                    setExperiments(exps);
                    addLog(`Loaded ${Object.keys(exps).length} experiments.`);
                    toast.success(`${Object.keys(exps).length} experiments loaded.`);
                  } catch { toast.error('Failed to parse experiment file'); }
                };
                r.readAsText(f);
                e.target.value = '';
              }} />
          </label>
          <div className="ad-exp-list">
            {Object.keys(experiments).length === 0
              ? <span className="dim">No experiments loaded.</span>
              : Object.keys(experiments).map(k => (
                <div key={k} className="ad-exp-item" title={k}
                  onDoubleClick={() => {
                    const selNode = nodes.find(n => n.selected);
                    if (!selNode) { toast('Select a node first'); return; }
                    setNodes(ns => ns.map(nd => nd.id === selNode.id
                      ? { ...nd, data: { ...nd.data, experiment: k } } : nd));
                    addLog(`${selNode.id} → experiment: "${k}"`);
                  }}>
                  {k}
                </div>
              ))}
          </div>
          <div className="dim" style={{fontSize:10,marginTop:4}}>Double-click experiment to assign to selected node</div>
        </div>

        {/* Canvas */}
        <div className="ad-canvas" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onNodeDoubleClick={onNodeDoubleClick}
            onNodeContextMenu={onNodeContextMenu}
            fitView
            deleteKeyCode="Delete"
            snapToGrid
            snapGrid={[20, 20]}
            style={{ background: 'transparent' }}
          >
            <Background variant={BackgroundVariant.Lines}
              gap={20} size={1} color="rgba(78,201,176,0.07)" />
            <Controls style={{ background:'#252526', border:'1px solid #3e3e42' }} />
            <MiniMap
              nodeColor={n => {
                const meta = NODE_TYPES_META[(n.data as FlowNodeData).nodeType];
                return meta?.color ?? '#555';
              }}
              style={{ background:'#1e1e1e', border:'1px solid #3e3e42' }} />
            <Panel position="top-right">
              <span className="ad-hint">
                {nodes.length} nodes · {edges.length} edges &nbsp;|&nbsp;
                Drag nodes · Connect handles · Del = delete selected
              </span>
            </Panel>
          </ReactFlow>
        </div>

        {/* Right sidebar — nodes list + log */}
        <Sidebar
          nodes={nodes}
          edges={edges}
          log={log}
          experiments={experiments}
          onSelectNode={(id) => {
            setNodes(ns => ns.map(n => ({ ...n, selected: n.id === id })));
          }}
          onRename={(id, name) => {
            setNodes(ns => ns.map(n => n.id === id ? { ...n, data: { ...n.data, label: name } } : n));
            addLog(`Renamed ${id} → "${name}"`);
          }}
          onDelete={(id) => {
            setNodes(ns => ns.filter(n => n.id !== id));
            setEdges(es => es.filter(e => e.source !== id && e.target !== id));
            addLog(`Deleted ${id}.`);
          }}
          onAssign={(id, exp) => {
            setNodes(ns => ns.map(n => n.id === id ? { ...n, data: { ...n.data, experiment: exp } } : n));
            addLog(`${id} → experiment: "${exp}"`);
          }}
        />
      </div>

      {/* Context menu */}
      {ctxMenu && (
        <div className="ad-ctx-menu" style={{ top: ctxMenu.y, left: ctxMenu.x }}
          onClick={e => e.stopPropagation()}>
          <div className="ad-ctx-title">{ctxMenu.nodeId}</div>
          <button onClick={ctxRename}>✏ Rename</button>
          <button onClick={ctxAssignExp}>🔗 Assign Experiment</button>
          <button className="danger" onClick={ctxDelete}>✕ Delete Node</button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function buildFlowPayload(
  nodes: any[], edges: any[],
  unitConfig: Record<string,unknown>,
  experiments: Record<string,unknown>,
) {
  const nodeMap: Record<string,unknown> = {};
  for (const n of nodes) {
    const connections: Record<string,string> = {};
    for (const e of edges.filter(e => e.source === n.id)) {
      const portNum = (e.sourceHandle ?? 'p0').replace('p','');
      connections[portNum] = e.target;
    }
    nodeMap[n.id] = {
      id: n.id, name: n.data.label, type: n.data.nodeType,
      x: Math.round(n.position.x), y: Math.round(n.position.y),
      experiment: n.data.experiment ?? null,
      connections,
    };
  }
  return { nodes: nodeMap, unit_config: unitConfig, experiments };
}
