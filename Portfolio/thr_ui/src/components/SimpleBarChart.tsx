/**
 * SimpleBarChart — lightweight SVG horizontal Pareto bar chart (zero dependencies).
 * Bars are sorted descending by value.
 */
import React from 'react';

export interface BarEntry {
  label: string;
  value: number;
  color?: string;
}

interface Props {
  data: BarEntry[];
  title?: string;
  /** Width reserved for bar area (px). Default 260. */
  barWidth?: number;
  /** Width reserved for labels (px). Default 160. */
  labelWidth?: number;
}

const PALETTE = [
  '#e05252', '#e07a52', '#e0a352', '#c8c052',
  '#52c87a', '#52a0e0', '#7a52e0', '#c052c0',
  '#52c8c8', '#a0c852',
];

export default function SimpleBarChart({ data, title, barWidth = 260, labelWidth = 160 }: Props) {
  if (!data.length) {
    return <div style={{ color: '#858585', fontSize: 12, padding: 8 }}>No chart data available.</div>;
  }

  const sorted   = [...data].sort((a, b) => b.value - a.value);
  const maxVal   = sorted[0].value || 1;
  const ROW_H    = 28;
  const PAD_V    = 6;
  const COUNT_W  = 46;
  const svgH     = sorted.length * ROW_H + PAD_V * 2;
  const svgW     = labelWidth + barWidth + COUNT_W;

  return (
    <div style={{ overflowX: 'auto' }}>
      {title && (
        <div style={{ fontSize: 12, fontWeight: 600, color: '#d4d4d4', marginBottom: 6 }}>{title}</div>
      )}
      <svg width={svgW} height={svgH} style={{ display: 'block', fontFamily: 'monospace' }}>
        {sorted.map((entry, i) => {
          const y     = PAD_V + i * ROW_H;
          const barW  = Math.max(2, (entry.value / maxVal) * barWidth);
          const label = entry.label.length > 20 ? entry.label.slice(0, 19) + '…' : entry.label;
          const fill  = entry.color ?? PALETTE[i % PALETTE.length];
          return (
            <g key={entry.label}>
              <text
                x={labelWidth - 8}
                y={y + ROW_H * 0.65}
                textAnchor="end"
                fill="#aaaaaa"
                fontSize={11}
              >{label}</text>
              <rect
                x={labelWidth}
                y={y + 4}
                width={barW}
                height={ROW_H - 10}
                fill={fill}
                rx={2}
                opacity={0.85}
              />
              <text
                x={labelWidth + barW + 5}
                y={y + ROW_H * 0.65}
                fill="#cccccc"
                fontSize={11}
              >{entry.value}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
