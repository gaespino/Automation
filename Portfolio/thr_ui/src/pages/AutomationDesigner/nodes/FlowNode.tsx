import { memo } from 'react';
import { Handle, Position, type NodeProps, type Node } from '@xyflow/react';
import './FlowNode.css';

/** Per-type configuration */
export const NODE_TYPES_META: Record<string, {
  label: string; symbol: string; color: string; ports: number[];
}> = {
  StartNode:              { label: 'Start',           symbol: '▶', color: '#16825d', ports: [0] },
  EndNode:                { label: 'End',              symbol: '■', color: '#c72e2e', ports: [] },
  SingleFailFlowInstance: { label: 'SingleFail',       symbol: '✕', color: '#1e5799', ports: [0,1,2,3] },
  AllFailFlowInstance:    { label: 'AllFail',          symbol: '❖', color: '#103d6e', ports: [0,1,2,3] },
  MajorityFailFlowInst:   { label: 'MajorityFail',    symbol: '½', color: '#5c2d91', ports: [0,1,2,3] },
  AdaptiveFlowInstance:   { label: 'Adaptive',        symbol: '◆', color: '#c07c00', ports: [0,3] },
  CharacterizationFI:     { label: 'Characterization', symbol:'◎', color: '#127d8b', ports: [0,3] },
  DataCollectionFI:       { label: 'DataCollection',  symbol: '⊕', color: '#1a7236', ports: [0,3] },
  AnalysisFlowInstance:   { label: 'Analysis',        symbol: '⊙', color: '#6e2f24', ports: [0,3] },
};

const PORT_COLORS: Record<number, string> = { 0:'#4ec9b0', 1:'#f44747', 2:'#ce9178', 3:'#9b9bff' };
const PORT_LABELS: Record<number, string> = { 0:'OK', 1:'Fail', 2:'Alt', 3:'Err' };

export type FlowNodeData = Record<string, unknown> & {
  label: string;
  nodeType: string;
  experiment?: string;
};

export type FlowNodeType = Node<FlowNodeData, 'flowNode'>;

function FlowNode({ data, selected }: NodeProps<FlowNodeType>) {
  const d = data as FlowNodeData;
  const meta = NODE_TYPES_META[d.nodeType as string] ?? { label: d.nodeType, symbol: '?', color: '#555', ports: [0] };
  const ports = meta.ports;
  const isStart = d.nodeType === 'StartNode';
  const isEnd   = d.nodeType === 'EndNode';

  return (
    <div
      className={`flow-node${selected ? ' selected' : ''}`}
      style={{ borderColor: meta.color, '--node-color': meta.color } as React.CSSProperties}
    >
      {/* INPUT handle (top) — hidden on StartNode */}
      {!isStart && (
        <Handle type="target" position={Position.Top} id="in" className="handle-in" />
      )}

      {/* Header strip */}
      <div className="fn-header" style={{ background: meta.color }}>
        <span className="fn-symbol">{meta.symbol}</span>
        <span className="fn-type">{meta.label}</span>
        {!isStart && <span className="fn-in-label">▲IN</span>}
      </div>

      {/* Body */}
      <div className="fn-body">
        <div className="fn-name">{d.label as string}</div>
        {d.experiment && (
          <div className="fn-exp">[{d.experiment as string}]</div>
        )}
      </div>

      {/* Output port strip (bottom) */}
      {!isEnd && ports.length > 0 && (
        <div className="fn-out-strip">
          <span className="fn-out-label">▼OUT</span>
          <div className="fn-ports">
            {ports.map(p => (
              <div key={p} className="fn-port-dot" title={`P${p}: ${PORT_LABELS[p]}`}
                style={{ background: PORT_COLORS[p] }}>
                <span>P{p}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Source handles per port (bottom) */}
      {!isEnd && ports.map((p, i) => {
        const pct = ports.length === 1
          ? 50
          : 20 + (i / (ports.length - 1)) * 60;
        return (
          <Handle
            key={`out-${p}`}
            type="source"
            position={Position.Bottom}
            id={`p${p}`}
            style={{ left: `${pct}%`, background: PORT_COLORS[p] }}
            className="handle-out"
          />
        );
      })}
    </div>
  );
}

export default memo(FlowNode);
