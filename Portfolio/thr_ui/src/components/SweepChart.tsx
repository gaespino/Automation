/**
 * SweepChart — SVG line chart for sweep / shmoo data.
 * X axis = parameter values (e.g. frequency steps).
 * Two series: Pass count (green) and Fail count (red).
 */
import React from 'react';

export interface SweepPoint {
  x: string | number;
  pass: number;
  fail: number;
}

interface Props {
  data: SweepPoint[];
  title?: string;
  xLabel?: string;
}

export default function SweepChart({ data, title, xLabel = 'Parameter Value' }: Props) {
  if (!data.length) {
    return <div style={{ color: '#858585', fontSize: 12, padding: 8 }}>No sweep data available.</div>;
  }

  const W       = 540;
  const H       = 210;
  const PAD     = { top: 24, right: 90, bottom: 52, left: 52 };
  const plotW   = W - PAD.left - PAD.right;
  const plotH   = H - PAD.top  - PAD.bottom;
  const maxVal  = Math.max(...data.map(d => d.pass + d.fail), 1);
  const n       = data.length;

  const xScale = (i: number) =>
    PAD.left + (n > 1 ? (i / (n - 1)) * plotW : plotW / 2);
  const yScale = (v: number) =>
    PAD.top + plotH - (v / maxVal) * plotH;

  const passLine = data.map((d, i) => `${xScale(i)},${yScale(d.pass)}`).join(' ');
  const failLine = data.map((d, i) => `${xScale(i)},${yScale(d.fail)}`).join(' ');

  // Y-axis tick values
  const ticks = [0, 0.25, 0.5, 0.75, 1].map(t => Math.round(t * maxVal));

  // Rotate X labels if many points
  const rotateLabels = n > 6;

  return (
    <div style={{ overflowX: 'auto' }}>
      {title && (
        <div style={{ fontSize: 12, fontWeight: 600, color: '#d4d4d4', marginBottom: 6 }}>{title}</div>
      )}
      <svg width={W} height={H} style={{ display: 'block', fontFamily: 'monospace', overflow: 'visible' }}>
        {/* Grid lines */}
        {ticks.map(t => {
          const y = yScale(t);
          return (
            <g key={t}>
              <line x1={PAD.left} y1={y} x2={PAD.left + plotW} y2={y}
                stroke="#2e2e2e" strokeWidth={1} strokeDasharray="3,3" />
              <text x={PAD.left - 6} y={y + 4} textAnchor="end" fill="#666" fontSize={9}>{t}</text>
            </g>
          );
        })}

        {/* Axes */}
        <line x1={PAD.left} y1={PAD.top}
              x2={PAD.left} y2={PAD.top + plotH} stroke="#555" />
        <line x1={PAD.left} y1={PAD.top + plotH}
              x2={PAD.left + plotW} y2={PAD.top + plotH} stroke="#555" />

        {/* Lines */}
        {n > 1 && <polyline points={passLine} fill="none" stroke="#4ec9b0" strokeWidth={2} />}
        {n > 1 && <polyline points={failLine} fill="none" stroke="#f44747" strokeWidth={2} />}

        {/* Data points + X labels */}
        {data.map((d, i) => {
          const cx   = xScale(i);
          const lblY = PAD.top + plotH + 14;
          const lbl  = String(d.x).slice(0, 10);
          return (
            <g key={i}>
              <circle cx={cx} cy={yScale(d.pass)} r={5} fill="#4ec9b0" stroke="#1e1e1e" strokeWidth={1}>
                <title>Pass: {d.pass}</title>
              </circle>
              <circle cx={cx} cy={yScale(d.fail)} r={5} fill="#f44747" stroke="#1e1e1e" strokeWidth={1}>
                <title>Fail: {d.fail}</title>
              </circle>
              {rotateLabels ? (
                <text x={cx} y={lblY} textAnchor="end" fill="#858585" fontSize={9}
                  transform={`rotate(-35,${cx},${lblY})`}>{lbl}</text>
              ) : (
                <text x={cx} y={lblY} textAnchor="middle" fill="#858585" fontSize={9}>{lbl}</text>
              )}
            </g>
          );
        })}

        {/* Y-axis label */}
        <text
          x={14} y={PAD.top + plotH / 2}
          textAnchor="middle" fill="#666" fontSize={9}
          transform={`rotate(-90,14,${PAD.top + plotH / 2})`}
        >Count</text>

        {/* X-axis label */}
        <text x={PAD.left + plotW / 2} y={H - 4}
          textAnchor="middle" fill="#666" fontSize={10}>{xLabel}</text>

        {/* Legend */}
        <circle cx={W - 78} cy={PAD.top + 6} r={5} fill="#4ec9b0" />
        <text x={W - 70} y={PAD.top + 10} fill="#4ec9b0" fontSize={10}>Pass</text>
        <circle cx={W - 78} cy={PAD.top + 22} r={5} fill="#f44747" />
        <text x={W - 70} y={PAD.top + 26} fill="#f44747" fontSize={10}>Fail</text>
      </svg>
    </div>
  );
}
