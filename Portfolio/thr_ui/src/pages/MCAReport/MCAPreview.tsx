/**
 * MCAPreview — structured inline viewer for a generated MCA report.
 *
 * Features:
 *   • VID filter — single text or multi-line list; filters rows across ALL tables simultaneously
 *   • Analysis sheet auto-split into collapsible sections:
 *       Root Cause  (VID, Runs, WW, Root Cause, Debug Hunts, Failing Area …)
 *       CHA / CORE / MEM / IO / OTHERS  (per-IP columns)
 *   • Optional MCA data tables (CHA_MCAs, CORE_MCAs, etc.) — checkboxes, off by default
 *   • Optional Pareto chart — shows failing-instance count per MCA tab, off by default
 *   • PDF export — prints the current filtered view in an executive report format
 */
import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import SimpleBarChart from '../../components/SimpleBarChart';
import type { BarEntry } from '../../components/SimpleBarChart';
import './style.css';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface SheetData {
  sheet: string;
  columns: string[];
  rows: (string | number | null)[][];
  total_rows: number;
}

interface Props {
  token: string;
  apiBase: string;   // e.g. '/api/mca'
  expFilter?: string[];  // optional experiment name filter (used when an Experiment column exists)
}

// ---------------------------------------------------------------------------
// Column classification patterns
// ---------------------------------------------------------------------------
const ROOT_PATTERNS: RegExp[] = [
  /visual.?id/i, /\bvid\b/i, /\bunit\b/i, /\bruns?\b/i,
  /work.?week/i, /\bww\b/i, /root.?cause/i, /debug/i,
  /fail.*area/i, /failing/i, /hunt/i,
];

const IP_GROUPS: Array<{ id: string; label: string; icon: string; pats: RegExp[] }> = [
  { id: 'CHA',   label: 'CHA',   icon: '⚡', pats: [/\bcha\b/i, /\bllc\b/i, /\bccf\b/i] },
  { id: 'CORE',  label: 'CORE',  icon: '💻', pats: [/\bcore\b/i, /\bcpu\b/i, /\bifu\b/i, /\bdcu\b/i] },
  { id: 'MEM',   label: 'MEM',   icon: '🧠', pats: [/\bmem\b/i, /\bimc\b/i, /\bddr\b/i, /\bhbm\b/i, /\bmc\b/i] },
  { id: 'IO',    label: 'IO',    icon: '🔌', pats: [/\bio\b/i, /\bpcie\b/i, /\biio\b/i, /\bhfi\b/i] },
];

function classifyCol(col: string): string {
  // Handle multi-level headers: "CHA / Count" → extract "CHA" as top-level
  const slashIdx = col.indexOf(' / ');
  const prefix = slashIdx >= 0 ? col.slice(0, slashIdx).trim() : col;

  // Check IP groups FIRST — prevents "CHA Fails" being swallowed by /failing/ root pattern
  for (const g of IP_GROUPS) {
    if (g.pats.some(p => p.test(prefix) || p.test(col))) return g.id;
  }
  // Root cause patterns second
  if (ROOT_PATTERNS.some(r => r.test(col))) return '__root';
  return 'OTHERS';
}

function isMcaSheet(name: string) {
  return (
    /_mca/i.test(name) ||
    /^ubox/i.test(name) ||
    /^portid/i.test(name) ||
    /^mca_/i.test(name)
  );
}

function findVidCol(columns: string[]): number {
  const pats = [/visual.?id/i, /\bvid\b/i, /\bunit\b/i];
  for (const p of pats) {
    const idx = columns.findIndex(c => p.test(c));
    if (idx >= 0) return idx;
  }
  return -1;
}

// ---------------------------------------------------------------------------
// Per-sheet drill-down column definitions
// Columns are listed in the order they should appear as chart options.
// DMR differences are handled via pattern fallbacks within each spec.
//   GNR/CWF: CORE col = "CORE", bank col = ErrorType, Compute field = "Compute"
//   DMR:     CORE col = "MODULE", bank col = "Bank",    Compute field = "CBB"
//            CHA renamed to CCF; MEM adds IMH column; IO uses IMH_CBB instead of IO
//   DMR CHA/CCF: use CBB+ENV+Instance combo pareto for more unique location keys
// ---------------------------------------------------------------------------
interface CombineFieldSpec { prefix: string; pats: RegExp[]; pad?: number; }
interface DrillColSpec { label: string; pats: RegExp[]; combineWith?: CombineFieldSpec[]; }
interface SheetDrillDef { match: RegExp; cols: DrillColSpec[]; }

const SHEET_DRILL_DEFS: SheetDrillDef[] = [
  // CHA / CCF MCAs
  {
    match: /cha.*mca|ccf.*mca/i,
    cols: [
      // DMR: CBB+ENV+Instance combo detected by presence of all three columns
      { label: 'CBB+ENV+Inst',  pats: [/^cbb$/i], combineWith: [
          { prefix: 'CBB',  pats: [/^cbb$/i]                  },
          { prefix: 'ENV',  pats: [/^env$/i]                  },
          { prefix: 'INST', pats: [/\binst(ance)?\b/i], pad: 2 },
        ],
      },
      // GNR/CWF fallback (single column)
      { label: 'CHA/CCF',      pats: [/^cha$/i, /^ccf$/i, /^env$/i] },
      { label: 'MC DECODE',    pats: [/mc.?decode/i] },
      { label: 'MC ADDR',      pats: [/mc.?addr/i] },
      { label: 'Orig Req',     pats: [/orig.?req/i, /orig.?request/i] },
      { label: 'SrcID',        pats: [/src.?id/i, /source.?id/i] },
      { label: 'Local Port',   pats: [/local.?port/i] },
      { label: 'Compute/CBB',  pats: [/^compute$/i, /^cbb$/i] },
    ],
  },
  // LLC MCAs
  {
    match: /llc.*mca/i,
    cols: [
      { label: 'LLC',          pats: [/^llc$/i] },
      { label: 'MC DECODE',    pats: [/mc.?decode/i] },
      { label: 'ADDR Way',     pats: [/addr.?way/i, /^way$/i] },
      { label: 'Compute/CBB',  pats: [/^compute$/i, /^cbb$/i] },
    ],
  },
  // CORE MCAs  (GNR/CWF: "CORE" + ErrorType;  DMR/CWF2: "MODULE" + "CORE" combo + Bank)
  {
    match: /core.*mca|^core/i,
    cols: [
      // DMR/CWF: Module+Core combo — fires only when both MODULE and CORE columns are present
      { label: 'Module+Core',  pats: [/^module$/i], combineWith: [
          { prefix: 'M', pats: [/^module$/i] },
          { prefix: 'C', pats: [/^core$/i]   },
        ],
      },
      { label: 'Core/Module',  pats: [/^core$/i, /^module$/i] },
      { label: 'Bank/ErrType', pats: [/\bbank\b/i, /error.?type/i, /err.?type/i] },
      { label: 'MCACOD',       pats: [/mca.?cod/i, /\bmcacod\b/i] },
      { label: 'Compute/CBB',  pats: [/^compute$/i, /^cbb$/i] },
    ],
  },
  // IO / IMH MCAs  (GNR/CWF: "IO";  DMR: "IMH_CBB")
  {
    match: /^io|imh|io.*mca/i,
    cols: [
      { label: 'IO/IMH',       pats: [/^io$/i, /^imh.?cbb$/i, /^imh$/i] },
      { label: 'MC DECODE',    pats: [/mc.?decode/i] },
      { label: 'MC ADDR',      pats: [/mc.?addr/i] },
    ],
  },
  // MEM MCAs  (DMR adds IMH column before Instance)
  {
    match: /mem.*mca|^mem/i,
    cols: [
      { label: 'Type',         pats: [/^type$/i] },
      { label: 'IMH',          pats: [/^imh$/i] },
      { label: 'MC DECODE',    pats: [/mc.?decode/i] },
      { label: 'MC ADDR',      pats: [/mc.?addr/i] },
    ],
  },
  // UBOX — FirstError - Location is most informative
  {
    match: /ubox/i,
    cols: [
      { label: 'Location',     pats: [/first.?error.*location/i, /firsterror/i, /\blocation\b/i] },
      { label: 'Module',       pats: [/\bmodule\b/i, /\bsource\b/i] },
    ],
  },
  // PortID sheets
  {
    match: /portid/i,
    cols: [
      { label: 'Port ID',      pats: [/\bport.?id\b/i, /\bport\b/i] },
      { label: 'MC DECODE',    pats: [/mc.?decode/i] },
    ],
  },
];

const GENERIC_DRILL_COLS: DrillColSpec[] = [
  { label: 'Module',   pats: [/\bmodule\b/i] },
  { label: 'Core',     pats: [/\bcore\b/i] },
  { label: 'Channel',  pats: [/\bch(annel)?\b/i] },
  { label: 'Location', pats: [/\blocation\b/i] },
  { label: 'Bank',     pats: [/\bbank\b/i] },
  { label: 'Port',     pats: [/\bport\b/i] },
];

/** Returns ordered [{label, colIdx, combineFields?}] for columns actually present in the sheet. */
function findDrillCols(
  sheetName: string,
  columns: string[],
): Array<{ label: string; colIdx: number; combineFields?: Array<{ prefix: string; idx: number; pad?: number }> }> {
  const def   = SHEET_DRILL_DEFS.find(d => d.match.test(sheetName));
  const specs = def ? def.cols : GENERIC_DRILL_COLS;
  const result: Array<{ label: string; colIdx: number; combineFields?: Array<{ prefix: string; idx: number; pad?: number }> }> = [];
  for (const spec of specs) {
    // Combination spec: all combineWith fields must be present
    if (spec.combineWith && spec.combineWith.length > 0) {
      const resolved: Array<{ prefix: string; idx: number; pad?: number }> = [];
      let allFound = true;
      for (const field of spec.combineWith) {
        const idx = columns.findIndex(c => field.pats.some(p => p.test(c)));
        if (idx < 0) { allFound = false; break; }
        resolved.push({ prefix: field.prefix, idx, pad: field.pad });
      }
      if (allFound && !result.some(r => r.label === spec.label)) {
        result.push({ label: spec.label, colIdx: resolved[0].idx, combineFields: resolved });
      }
      // Always continue to next spec — single-col fallbacks remain available
      continue;
    }
    // Normal single-column spec
    for (const p of spec.pats) {
      const idx = columns.findIndex(c => p.test(c));
      if (idx >= 0) {
        if (!result.some(r => r.colIdx === idx && !r.combineFields))
          result.push({ label: spec.label, colIdx: idx });
        break;
      }
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// Chart download helper — SVG element → Canvas → PNG / JPG blob download
// ---------------------------------------------------------------------------
function downloadChartContainer(container: HTMLElement | null, filename: string, fmt: 'png' | 'jpg') {
  if (!container) return;
  const svg = container.querySelector('svg');
  if (!svg) return;
  const clone = svg.cloneNode(true) as SVGSVGElement;
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  const w = svg.clientWidth  || parseInt(svg.getAttribute('width')  ?? '500');
  const h = svg.clientHeight || parseInt(svg.getAttribute('height') ?? '300');
  const title = container.querySelector<HTMLElement>('[data-chart-title]')?.textContent ?? '';
  const titleH = title ? 22 : 0;
  const svgData = new XMLSerializer().serializeToString(clone);
  const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
  const url  = URL.createObjectURL(blob);
  const img  = new Image();
  img.onload = () => {
    const canvas = document.createElement('canvas');
    canvas.width  = w * 2;
    canvas.height = (h + titleH) * 2;
    const ctx = canvas.getContext('2d')!;
    ctx.scale(2, 2);
    ctx.fillStyle = '#1e1e1e';
    ctx.fillRect(0, 0, w, h + titleH);
    if (title) {
      ctx.fillStyle = '#d4d4d4';
      ctx.font = '600 12px monospace';
      ctx.fillText(title, 4, 15);
    }
    ctx.drawImage(img, 0, titleH, w, h);
    URL.revokeObjectURL(url);
    const mime = fmt === 'jpg' ? 'image/jpeg' : 'image/png';
    const a = document.createElement('a');
    a.href     = canvas.toDataURL(mime, 0.95);
    a.download = filename;
    a.click();
  };
  img.src = url;
}

// ---------------------------------------------------------------------------
// Heatmap — VID × MCA-tab fail count matrix
// ---------------------------------------------------------------------------
interface HeatmapProps {
  vids:   string[];
  sheets: string[];
  matrix: number[][];   // matrix[vidIdx][sheetIdx] = fail count
}
function HeatmapChart({ vids, sheets, matrix }: HeatmapProps) {
  const CW  = 46;   // cell width
  const CH  = 18;   // cell height
  const LW  = 150;  // label column width
  const HH  = 64;   // header height (rotated labels)
  const PAD = 10;

  const maxVal = Math.max(1, ...matrix.flat());

  const cellColor = (val: number): string => {
    if (val === 0) return '#282828';
    const t = val / maxVal;
    const r = Math.round(90  + t * (224 - 90));
    const g = Math.round(26  + t * (82  - 26));
    const b = Math.round(26  + t * (82  - 26));
    return `rgb(${r},${g},${b})`;
  };

  const W = LW + sheets.length * CW + PAD;
  const H = HH + vids.length * CH + PAD + 28; // +28 for legend

  return (
    <svg width={W} height={H} style={{ background: '#1e1e1e', display: 'block' }}>

      {/* Sheet header labels — rotated 45° */}
      {sheets.map((s, si) => (
        <g key={s} transform={`translate(${LW + si * CW + CW / 2}, ${HH - 4})`}>
          <text
            transform="rotate(-45)"
            textAnchor="start"
            style={{ fontSize: 10, fill: '#bbbbbb', fontFamily: 'monospace' }}
          >{s}</text>
        </g>
      ))}

      {/* VID labels — Y axis */}
      {vids.map((v, vi) => (
        <text
          key={v}
          x={LW - 6}
          y={HH + vi * CH + CH / 2 + 4}
          textAnchor="end"
          style={{ fontSize: 10, fill: '#aaaaaa', fontFamily: 'monospace' }}
        >{v.length > 18 ? v.slice(0, 17) + '…' : v}</text>
      ))}

      {/* Cells */}
      {vids.map((v, vi) =>
        sheets.map((s, si) => {
          const val = matrix[vi]?.[si] ?? 0;
          const x   = LW + si * CW;
          const y   = HH + vi * CH;
          return (
            <g key={`${vi}-${si}`}>
              <rect x={x} y={y} width={CW - 1} height={CH - 1} fill={cellColor(val)} rx={2} />
              {val > 0 && (
                <text
                  x={x + CW / 2}
                  y={y + CH / 2 + 4}
                  textAnchor="middle"
                  style={{ fontSize: 9, fill: val / maxVal > 0.45 ? '#fff' : '#ddd', fontFamily: 'monospace' }}
                >{val}</text>
              )}
              <title>{v} — {s}: {val} fail{val !== 1 ? 's' : ''}</title>
            </g>
          );
        })
      )}

      {/* Legend */}
      {(() => {
        const ly = HH + vids.length * CH + 10;
        const steps = 5;
        const sw = 26;
        return (
          <g>
            <text x={LW} y={ly + 10} style={{ fontSize: 9, fill: '#777', fontFamily: 'monospace' }}>0</text>
            {Array.from({ length: steps }, (_, i) => {
              const t = (i + 1) / steps;
              const val = Math.round(t * maxVal);
              return (
                <g key={i} transform={`translate(${LW + 16 + i * sw}, ${ly})`}>
                  <rect width={sw - 1} height={12} fill={cellColor(val)} rx={2} />
                  {i === steps - 1 && (
                    <text x={sw / 2} y={22} textAnchor="middle" style={{ fontSize: 9, fill: '#777', fontFamily: 'monospace' }}>{maxVal}</text>
                  )}
                </g>
              );
            })}
          </g>
        );
      })()}
    </svg>
  );
}

const PAGE = 300;

// ---------------------------------------------------------------------------
// Mini table for a subset of columns from a full SheetData — with resizable columns
// ---------------------------------------------------------------------------
const MIN_COL_W = 50;
const DEF_COL_W = 120;

function SectionTable({
  allCols, colIdxs, rows, vidSet, vidMultiMode, vidIdx,
}: {
  allCols: string[];
  colIdxs: number[];
  rows: (string | number | null)[][];
  vidSet: Set<string>;
  vidMultiMode: boolean;
  vidIdx: number;
}) {
  const filtered = useMemo(() => {
    if (vidSet.size === 0 || vidIdx < 0) return rows;
    return rows.filter(r => vidPassesFilter(r, vidIdx, vidSet, vidMultiMode));
  }, [rows, vidSet, vidMultiMode, vidIdx]);

  const [colWidths, setColWidths] = useState<Record<number, number>>({});
  const dragRef = useRef<{ col: number; startX: number; startW: number } | null>(null);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragRef.current) return;
      const delta = e.clientX - dragRef.current.startX;
      const newW  = Math.max(MIN_COL_W, dragRef.current.startW + delta);
      setColWidths(w => ({ ...w, [dragRef.current!.col]: newW }));
    };
    const onUp = () => { dragRef.current = null; };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup',  onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup',  onUp);
    };
  }, []);

  if (!colIdxs.length) {
    return <span style={{ color: '#858585', fontSize: 11 }}>No matching columns.</span>;
  }

  const shown = filtered.slice(0, PAGE);

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="ev-table" style={{ fontSize: 11, tableLayout: 'fixed' }}>
        <thead>
          <tr>
            {colIdxs.map(i => {
              const w = colWidths[i] ?? DEF_COL_W;
              return (
                <th key={i} style={{ padding: 0, position: 'relative', width: w, maxWidth: w }}>
                  <div style={{ padding: '4px 20px 4px 8px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {allCols[i]}
                  </div>
                  <div
                    onMouseDown={e => {
                      e.preventDefault();
                      dragRef.current = { col: i, startX: e.clientX, startW: colWidths[i] ?? DEF_COL_W };
                    }}
                    style={{
                      position: 'absolute', right: 0, top: 0, bottom: 0, width: 6,
                      cursor: 'col-resize', background: 'transparent',
                      borderRight: '2px solid #444',
                    }}
                  />
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {shown.map((row, ri) => (
            <tr key={ri} className={ri % 2 === 1 ? 'ev-row-alt' : ''}>
              {colIdxs.map(ci => {
                const w = colWidths[ci] ?? DEF_COL_W;
                return (
                  <td key={ci} style={{ padding: '3px 8px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: w }}>
                    {String(row[ci] ?? '')}
                  </td>
                );
              })}
            </tr>
          ))}
          {filtered.length === 0 && (
            <tr>
              <td colSpan={colIdxs.length} style={{ color: '#858585', fontSize: 11, padding: 8, textAlign: 'center' }}>
                No rows match filter.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      {filtered.length > PAGE && (
        <div style={{ fontSize: 10, color: '#858585', padding: '3px 0' }}>
          Showing {PAGE} of {filtered.length} rows.
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Collapsible section wrapper
// ---------------------------------------------------------------------------
function Section({
  id, icon, label, count, collapsed, onToggle, children,
}: {
  id: string; icon: string; label: string; count?: number;
  collapsed: boolean; onToggle: () => void; children: React.ReactNode;
}) {
  return (
    <div className="mca-section">
      <div className="mca-section-header" onClick={onToggle}>
        <span className="mca-section-chevron">{collapsed ? '▸' : '▾'}</span>
        <span>{icon} {label}</span>
        {count !== undefined && (
          <span className="mca-section-count">({count} rows)</span>
        )}
      </div>
      {!collapsed && <div className="mca-section-body">{children}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// VID filter helpers
// ---------------------------------------------------------------------------
/** Parse VID filter text into a normalised Set. Multi-line = exact-match list mode. */
function parseVidFilter(text: string): { set: Set<string>; multi: boolean } {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  if (lines.length <= 1) {
    return { set: new Set(lines.map(l => l.toLowerCase())), multi: false };
  }
  return { set: new Set(lines.map(l => l.toLowerCase())), multi: true };
}

/** Returns true if a row passes the VID filter. */
function vidPassesFilter(
  row: (string | number | null)[],
  vidIdx: number,
  filterSet: Set<string>,
  multiMode: boolean,
): boolean {
  if (filterSet.size === 0) return true;
  if (vidIdx < 0) return true;
  const val = String(row[vidIdx] ?? '').trim().toLowerCase();
  if (multiMode) return filterSet.has(val);     // exact match from list
  const term = [...filterSet][0] ?? '';
  return val.includes(term);                    // substring match
}

// ---------------------------------------------------------------------------
// PDF export helper
// ---------------------------------------------------------------------------
function triggerPdfExport(containerRef: React.RefObject<HTMLDivElement | null>, title: string) {
  const el = containerRef.current;
  if (!el) return;

  const timestamp = new Date().toLocaleString();

  // Collect SVG chart elements → blob URLs so they survive the print window
  const svgEls = Array.from(el.querySelectorAll<SVGSVGElement>('svg'));
  const svgMap = new Map<SVGSVGElement, string>();
  svgEls.forEach(svg => {
    const clone = svg.cloneNode(true) as SVGSVGElement;
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    const blob = new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' });
    svgMap.set(svg, URL.createObjectURL(blob));
  });

  // Clone the visible tree and replace SVGs with <img> placeholders
  const cloned = el.cloneNode(true) as HTMLElement;
  const clonedSvgs = Array.from(cloned.querySelectorAll<SVGSVGElement>('svg'));
  clonedSvgs.forEach((svg, i) => {
    const url = svgMap.get(svgEls[i]);
    if (!url) return;
    const img = document.createElement('img');
    img.src = url;
    img.style.cssText = 'max-width:100%;height:auto;display:block;margin:4px 0;';
    svg.parentElement?.replaceChild(img, svg);
  });

  // Hide interactive controls from the clone
  cloned.querySelectorAll<HTMLElement>('button, input, textarea, .mca-preview-controls').forEach(
    el => { el.style.display = 'none'; },
  );

  const html = `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>MCA Report – ${title}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',Arial,sans-serif;font-size:10pt;color:#111;background:#fff;padding:24px 32px}
  h1{font-size:15pt;font-weight:700;margin-bottom:4px;color:#1a1a2e}
  .rpt-meta{font-size:9pt;color:#666;margin-bottom:16px;border-bottom:1px solid #ccc;padding-bottom:6px}
  .mca-sections{margin-bottom:16px}
  .mca-sections-title{font-size:11pt;font-weight:700;color:#1a1a2e;border-bottom:2px solid #1a1a2e;
    margin-bottom:8px;padding-bottom:3px}
  .mca-section{margin-bottom:10px;page-break-inside:avoid}
  .mca-section-header{font-size:9.5pt;font-weight:600;background:#ececf5;padding:3px 8px;
    border-left:3px solid #4a4aaa;margin-bottom:3px}
  .mca-section-chevron,.mca-section-count{display:none}
  .mca-section-body{font-size:8.5pt}
  table{border-collapse:collapse;width:100%;font-size:8pt;margin-bottom:4px}
  th{background:#1a1a2e;color:#fff;padding:2px 5px;text-align:left;border:1px solid #ccc;white-space:nowrap}
  td{border:1px solid #ddd;padding:2px 5px;white-space:nowrap;max-width:200px;overflow:hidden;text-overflow:ellipsis}
  tr:nth-child(even) td{background:#f5f5ff}
  img{max-width:100%;height:auto;display:block;margin:4px 0}
  .mca-preview-controls{display:none!important}
  @media print{body{padding:10px 14px}h1{font-size:13pt}}
</style></head><body>
<h1>MCA Analysis Report</h1>
<div class="rpt-meta">Filter: <b>${title}</b> &nbsp;|&nbsp; Generated: ${timestamp}</div>
${cloned.innerHTML}
</body></html>`;

  const win = window.open('', '_blank', 'width=1050,height=860');
  if (!win) { alert('Pop-up blocked – please allow pop-ups and retry.'); return; }
  win.document.open();
  win.document.write(html);
  win.document.close();
  win.onload = () => {
    svgMap.forEach(url => URL.revokeObjectURL(url));
    setTimeout(() => { win.focus(); win.print(); }, 400);
  };
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const CHART_VIEW_TABS    = '__tabs__';
const CHART_VIEW_VIDS    = '__vids__';
const CHART_VIEW_HEATMAP = '__heatmap__';

export default function MCAPreview({ token, apiBase, expFilter }: Props) {
  const [allSheets,    setAllSheets]    = useState<string[]>([]);
  const [analysisData, setAnalysisData] = useState<SheetData | null>(null);
  const [mcaData,      setMcaData]      = useState<Record<string, SheetData>>({});
  const [loadingBusy,  setLoadingBusy]  = useState<Set<string>>(new Set());

  // UI state
  const [vidFilter,     setVidFilter]     = useState('');
  const [vidMultiMode,  setVidMultiMode]  = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showMcaTabs, setShowMcaTabs] = useState<Record<string, boolean>>({});
  const [showCharts,      setShowCharts]      = useState(false);
  const [selectedCharts,  setSelectedCharts]  = useState<Set<string>>(new Set([CHART_VIEW_TABS]));
  const [collapsed,       setCollapsed]       = useState<Set<string>>(new Set());
  const [loadingAna,  setLoadingAna]  = useState(false);
  const [error,       setError]       = useState('');

  // -------------------------------------------------------------------------
  // Load sheet list
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!token) return;
    setError('');
    fetch(`${apiBase}/sheets?token=${encodeURIComponent(token)}`)
      .then(r => r.json())
      .then((d: Record<string, string[]>) => {
        const names: string[] = [];
        Object.values(d).forEach(arr => {
          if (Array.isArray(arr)) arr.forEach(n => { if (!names.includes(n)) names.push(n); });
        });
        setAllSheets(names);
      })
      .catch(e => setError(`Cannot load sheets: ${e.message}`));
  }, [token, apiBase]);

  const analysisSheet = useMemo(
    // Prefer exact "Analysis" match; fall back to any sheet containing "analysis"
    () =>
      allSheets.find(s => /^analysis$/i.test(s)) ??
      allSheets.find(s => /analysis/i.test(s)) ??
      '',
    [allSheets],
  );
  const mcaSheets = useMemo(
    () => allSheets.filter(s => isMcaSheet(s) && !/analysis/i.test(s)),
    [allSheets],
  );

  // -------------------------------------------------------------------------
  // Load Analysis sheet automatically when identified
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!analysisSheet || !token) return;
    setLoadingAna(true);
    fetch(`${apiBase}/sheet_data?token=${encodeURIComponent(token)}&sheet=${encodeURIComponent(analysisSheet)}&max_rows=5000`)
      .then(r => r.json())
      .then((d: SheetData) => setAnalysisData(d))
      .catch(e => setError(`Cannot load Analysis: ${e.message}`))
      .finally(() => setLoadingAna(false));
  }, [analysisSheet, token, apiBase]);

  // -------------------------------------------------------------------------
  // Load individual MCA sheet on demand
  // -------------------------------------------------------------------------
  const loadSheet = useCallback(async (sheet: string) => {
    if (mcaData[sheet] || loadingBusy.has(sheet)) return;
    setLoadingBusy(s => { const n = new Set(s); n.add(sheet); return n; });
    try {
      const r = await fetch(
        `${apiBase}/sheet_data?token=${encodeURIComponent(token)}&sheet=${encodeURIComponent(sheet)}&max_rows=5000`,
      );
      const d: SheetData = await r.json();
      setMcaData(prev => ({ ...prev, [sheet]: d }));
    } catch { /* swallow */ } finally {
      setLoadingBusy(s => { const n = new Set(s); n.delete(sheet); return n; });
    }
  }, [mcaData, loadingBusy, token, apiBase]);

  // Load sheets toggled on via checkboxes
  useEffect(() => {
    Object.entries(showMcaTabs).forEach(([s, on]) => { if (on) loadSheet(s); });
  }, [showMcaTabs]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load all MCA sheets when charts toggled on
  useEffect(() => {
    if (showCharts) mcaSheets.forEach(s => loadSheet(s));
  }, [showCharts, mcaSheets]); // eslint-disable-line react-hooks/exhaustive-deps

  // -------------------------------------------------------------------------
  // Derive: column groups for Analysis sheet
  // -------------------------------------------------------------------------
  const analysisGroups = useMemo(() => {
    if (!analysisData) return null;
    const buckets: Record<string, number[]> = {};
    analysisData.columns.forEach((col, idx) => {
      const key = classifyCol(col);
      (buckets[key] ??= []).push(idx);
    });
    return buckets;
  }, [analysisData]);

  const vidIdx = useMemo(
    () => (analysisData ? findVidCol(analysisData.columns) : -1),
    [analysisData],
  );

  // Parsed VID filter
  const vidParsed = useMemo(() => parseVidFilter(vidFilter), [vidFilter]);

  // VID-filtered rows for analysis
  // Detect experiment column in analysis data (used when expFilter is active)
  const expColIdx = useMemo(() => {
    if (!analysisData || !expFilter?.length) return -1;
    return analysisData.columns.findIndex(c => /experiment|test.?name|test.?id/i.test(c));
  }, [analysisData, expFilter]);

  const anaRows = useMemo(() => {
    if (!analysisData) return [];
    let rows = analysisData.rows;
    if (expFilter?.length && expColIdx >= 0) {
      const set = new Set(expFilter.map(e => e.toLowerCase()));
      rows = rows.filter(r => set.has(String(r[expColIdx] ?? '').toLowerCase()));
    }
    if (vidParsed.set.size === 0 || vidIdx < 0) return rows;
    return rows.filter(r => vidPassesFilter(r, vidIdx, vidParsed.set, vidParsed.multi));
  }, [analysisData, vidParsed, vidIdx, expFilter, expColIdx]);

  // VID-filtered rows for a given MCA sheet (also applies expFilter if experiment column found)
  const mcaRows = useCallback((sheet: string) => {
    const d = mcaData[sheet];
    if (!d) return [];
    let rows = d.rows;
    if (expFilter?.length) {
      const ei = d.columns.findIndex(c => /experiment|test.?name|test.?id/i.test(c));
      if (ei >= 0) {
        const set = new Set(expFilter.map(e => e.toLowerCase()));
        rows = rows.filter(r => set.has(String(r[ei] ?? '').toLowerCase()));
      }
    }
    if (vidParsed.set.size === 0) return rows;
    const vi = findVidCol(d.columns);
    if (vi < 0) return rows;
    return rows.filter(r => vidPassesFilter(r, vi, vidParsed.set, vidParsed.multi));
  }, [mcaData, vidParsed, expFilter]);

  const toggleSection = (id: string) =>
    setCollapsed(s => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  const toggleChart = useCallback((id: string) =>
    setSelectedCharts(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    }), []);

  const chartRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  const batchDownload = useCallback((fmt: 'png' | 'jpg') => {
    let delay = 0;
    for (const id of selectedCharts) {
      const el = chartRefs.current.get(id);
      if (!el) continue;
      const name = id === CHART_VIEW_TABS
        ? 'mca_fails_per_tab'
        : id.replace('::', '_').replace(/[^a-zA-Z0-9_-]/g, '_');
      setTimeout(() => downloadChartContainer(el, `${name}.${fmt}`, fmt), delay);
      delay += 350;
    }
  }, [selectedCharts]);

  // Pareto data: unique failing VID instances per MCA tab (with VID filter)
  const paretoData = useMemo<BarEntry[]>(() => {
    return mcaSheets
      .filter(s => mcaData[s])
      .map(s => {
        const d    = mcaData[s];
        const rows = mcaRows(s);
        const vi = findVidCol(d.columns);
        const val = vi >= 0
          ? new Set(rows.map(r => r[vi]).filter(v => v != null && String(v).trim() !== '')).size
          : rows.length;
        return { label: s, value: val };
      })
      .filter(e => e.value > 0)
      .sort((a, b) => b.value - a.value);
  }, [mcaSheets, mcaData, mcaRows]);

  // Drill-down paretos: multiple columns per sheet
  type DrillColEntry = {
    label: string; colName: string; colIdx: number; entries: BarEntry[];
    combineFields?: Array<{ prefix: string; idx: number; pad?: number }>;
  };
  const drillData = useMemo<Record<string, DrillColEntry[]>>(() => {
    const result: Record<string, DrillColEntry[]> = {};
    for (const s of mcaSheets) {
      const d = mcaData[s];
      if (!d) continue;
      const drillCols = findDrillCols(s, d.columns);
      const rows      = mcaRows(s);
      const colEntries: DrillColEntry[] = [];
      for (const { label, colIdx, combineFields } of drillCols) {
        const counts: Record<string, number> = {};
        if (combineFields && combineFields.length > 0) {
          // DMR combo: build "CBBx_ENVy_INSTzz" keys from multiple columns
          rows.forEach(r => {
            const parts = combineFields.map(({ prefix, idx, pad }) => {
              const v = String(r[idx] ?? '').trim();
              if (!v || v === 'N/A' || v === 'nan' || v === 'None') return null;
              const padded = pad ? v.padStart(pad, '0') : v;
              return `${prefix}${padded}`;
            });
            if (parts.some(p => p === null)) return; // skip if any field missing
            const key = parts.join('_');
            counts[key] = (counts[key] ?? 0) + 1;
          });
        } else {
          rows.forEach(r => {
            const v = String(r[colIdx] ?? '').trim();
            if (v && v !== 'N/A' && v !== 'nan' && v !== 'None')
              counts[v] = (counts[v] ?? 0) + 1;
          });
        }
        const entries = Object.entries(counts)
          .map(([lbl, value]) => ({ label: lbl, value }))
          .filter(e => e.value > 0)
          .sort((a, b) => b.value - a.value)
          .slice(0, 30);
        if (entries.length > 0)
          colEntries.push({ label, colName: d.columns[colIdx], colIdx, entries, combineFields });
      }
      if (colEntries.length > 0) result[s] = colEntries;
    }
    return result;
  }, [mcaSheets, mcaData, mcaRows]);

  // Fails per VID: total fail-row occurrences per unit across all MCA tabs
  const vidFailData = useMemo<BarEntry[]>(() => {
    const counts: Record<string, number> = {};
    for (const s of mcaSheets) {
      const d = mcaData[s];
      if (!d) continue;
      const vi = findVidCol(d.columns);
      if (vi < 0) continue;
      mcaRows(s).forEach(r => {
        const v = String(r[vi] ?? '').trim();
        if (v && v !== 'N/A' && v !== 'nan' && v !== 'None')
          counts[v] = (counts[v] ?? 0) + 1;
      });
    }
    return Object.entries(counts)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 50);
  }, [mcaSheets, mcaData, mcaRows]);

  // Multi-IP heatmap: VIDs that fail in 2+ MCA tabs
  const heatmapData = useMemo(() => {
    const sheets = mcaSheets.filter(s => mcaData[s]);
    const vidSheetCounts: Record<string, Record<string, number>> = {};
    for (const s of sheets) {
      const d = mcaData[s];
      if (!d) continue;
      const vi = findVidCol(d.columns);
      if (vi < 0) continue;
      mcaRows(s).forEach(r => {
        const v = String(r[vi] ?? '').trim();
        if (v && v !== 'N/A' && v !== 'nan' && v !== 'None') {
          (vidSheetCounts[v] ??= {})[s] = (vidSheetCounts[v][s] ?? 0) + 1;
        }
      });
    }
    // Keep only VIDs failing in 2+ sheets; sort by sheet-count desc then total count
    const multiVids = Object.entries(vidSheetCounts)
      .filter(([, sc]) => Object.keys(sc).length >= 2)
      .sort((a, b) => {
        const sd = Object.keys(b[1]).length - Object.keys(a[1]).length;
        if (sd !== 0) return sd;
        return Object.values(b[1]).reduce((x, y) => x + y, 0)
             - Object.values(a[1]).reduce((x, y) => x + y, 0);
      })
      .slice(0, 40)
      .map(([v]) => v);
    const matrix = multiVids.map(v => sheets.map(s => vidSheetCounts[v]?.[s] ?? 0));
    return { vids: multiVids, sheets, matrix };
  }, [mcaSheets, mcaData, mcaRows]);

  // Reset selections and refs when sheets change
  useEffect(() => {
    chartRefs.current.clear();
    setSelectedCharts(new Set([CHART_VIEW_TABS]));
  }, [mcaSheets]); // eslint-disable-line react-hooks/exhaustive-deps

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  if (!token) return null;
  if (error)  return <div className="ev-error">{error}</div>;

  const vidActiveCount = vidParsed.set.size;
  const reportTitle = vidActiveCount > 0
    ? (vidParsed.multi ? `${vidActiveCount} VID(s)` : [...vidParsed.set][0])
    : 'All Units';

  // Ordered analysis sections
  const sectionOrder: Array<{ id: string; icon: string; label: string }> = [
    { id: '__root', icon: '🔍', label: 'Root Cause' },
    ...IP_GROUPS.map(g => ({ id: g.id, icon: g.icon, label: g.label })),
    { id: 'OTHERS', icon: '📦', label: 'Others' },
  ];

  return (
    <div className="mca-preview" ref={containerRef}>

      {/* ── Controls bar ─────────────────────────────────────────────────── */}
      <div className="mca-preview-controls">
        <div className="mca-preview-vid-row">
          <span style={{ fontSize: 11, color: '#858585', whiteSpace: 'nowrap' }}>🔍 Filter VID:</span>

          {vidMultiMode ? (
            <textarea
              value={vidFilter}
              onChange={e => setVidFilter(e.target.value)}
              placeholder={`One VID per line…\nD5HC576100141\nD5HC576100142`}
              rows={4}
              style={{ flex: 1, minWidth: 180, fontSize: 11, fontFamily: 'monospace',
                       resize: 'vertical', padding: '4px 6px' }}
            />
          ) : (
            <input
              value={vidFilter}
              onChange={e => setVidFilter(e.target.value)}
              placeholder="Type VID to filter all tables…"
              style={{ flex: 1, minWidth: 180, fontSize: 12 }}
            />
          )}

          {vidFilter && (
            <button className="btn" style={{ padding: '2px 8px' }} onClick={() => setVidFilter('')}>✕</button>
          )}
          <button
            className={`btn${vidMultiMode ? ' primary' : ''}`}
            style={{ padding: '2px 8px', fontSize: 11, whiteSpace: 'nowrap' }}
            onClick={() => { setVidMultiMode(m => !m); }}
            title={vidMultiMode ? 'Switch to single-VID search' : 'Switch to multi-VID list mode'}
          >
            {vidMultiMode ? '— Single' : '☰ List'}
          </button>
          {vidActiveCount > 0 && (
            <span style={{ fontSize: 10, color: '#0e7a0d', whiteSpace: 'nowrap' }}>
              {vidParsed.multi ? `${vidActiveCount} VIDs` : `"${[...vidParsed.set][0]}"`}
            </span>
          )}
        </div>

        <div className="mca-preview-options-row">
          {mcaSheets.length > 0 && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontSize: 11, color: '#858585' }}>MCA Tables:</span>
              {mcaSheets.map(s => (
                <label key={s} className="check-label" style={{ fontSize: 11 }}>
                  <input
                    type="checkbox"
                    checked={!!showMcaTabs[s]}
                    onChange={() => setShowMcaTabs(prev => ({ ...prev, [s]: !prev[s] }))}
                  />
                  {s}
                </label>
              ))}
            </div>
          )}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 4, alignItems: 'center' }}>
            <label className="check-label" style={{ fontSize: 11 }}>
              <input type="checkbox" checked={showCharts} onChange={() => setShowCharts(v => !v)} />
              📊 Charts
            </label>
            <button
              className="btn"
              style={{ fontSize: 11, padding: '2px 10px', background: '#5a2d82', borderColor: '#7a3daa', color: '#fff' }}
              onClick={() => triggerPdfExport(containerRef, reportTitle)}
              title="Export current view as PDF"
            >
              📄 PDF
            </button>
          </div>
        </div>
      </div>

      {/* ── Analysis section ─────────────────────────────────────────────── */}
      {loadingAna && (
        <div style={{ padding: 12, color: '#858585', fontSize: 12 }}>⏳ Loading Analysis sheet…</div>
      )}

      {analysisData && !loadingAna && (
        <div className="mca-sections">
          <div className="mca-sections-title">📊 Analysis — {anaRows.length} rows{vidParsed.set.size > 0 ? ` (filtered)` : ''}</div>

          {sectionOrder.map(({ id, icon, label }) => {
            const idxs = analysisGroups?.[id] ?? [];
            if (!idxs.length) return null;
            // Always lead with VID column in every section (if not already present)
            const colIdxs = (vidIdx >= 0 && !idxs.includes(vidIdx)) ? [vidIdx, ...idxs] : idxs;
            return (
              <Section
                key={id}
                id={id}
                icon={icon}
                label={label}
                count={anaRows.length}
                collapsed={collapsed.has(id)}
                onToggle={() => toggleSection(id)}
              >
                <SectionTable
                  allCols={analysisData.columns}
                  colIdxs={colIdxs}
                  rows={analysisData.rows}
                  vidSet={vidParsed.set}
                  vidMultiMode={vidParsed.multi}
                  vidIdx={vidIdx}
                />
              </Section>
            );
          })}

          {/* Fallback: if no IP/Root sections matched, show one combined table */}
          {analysisGroups &&
            !['__root', 'CHA', 'CORE', 'MEM', 'IO'].some(id => (analysisGroups[id]?.length ?? 0) > 0) && (
            <Section
              id="raw"
              icon="📋"
              label="All Columns"
              count={anaRows.length}
              collapsed={collapsed.has('raw')}
              onToggle={() => toggleSection('raw')}
            >
              <div style={{ fontSize: 10, color: '#858585', marginBottom: 6 }}>
                Column names did not match known IP patterns — showing all {analysisData.columns.length} columns.
              </div>
              <SectionTable
                allCols={analysisData.columns}
                colIdxs={analysisData.columns.map((_, i) => i)}
                rows={analysisData.rows}
                vidSet={vidParsed.set}
                vidMultiMode={vidParsed.multi}
                vidIdx={vidIdx}
              />
            </Section>
          )}
        </div>
      )}

      {/* ── Optional MCA data tables ──────────────────────────────────────── */}
      {mcaSheets.some(s => showMcaTabs[s]) && (
        <div className="mca-sections" style={{ marginTop: 10 }}>
          <div className="mca-sections-title">🗄 MCA Data Tables</div>
          {mcaSheets.filter(s => showMcaTabs[s]).map(sheet => {
            const d    = mcaData[sheet];
            const busy = loadingBusy.has(sheet);
            const rows = mcaRows(sheet);
            const key  = `mca_${sheet}`;
            return (
              <Section
                key={key}
                id={key}
                icon="🗃"
                label={sheet}
                count={d ? rows.length : undefined}
                collapsed={collapsed.has(key)}
                onToggle={() => toggleSection(key)}
              >
                {busy && <div style={{ padding: 8, fontSize: 11, color: '#858585' }}>⏳ Loading…</div>}
                {d && (
                  <SectionTable
                    allCols={d.columns}
                    colIdxs={d.columns.map((_, i) => i)}
                    rows={d.rows}
                    vidSet={vidParsed.set}
                    vidMultiMode={vidParsed.multi}
                    vidIdx={findVidCol(d.columns)}
                  />
                )}
              </Section>
            );
          })}
        </div>
      )}

      {/* ── Pareto charts ────────────────────────────────────────────────── */}
      {showCharts && (
        <div className="mca-sections" style={{ marginTop: 10 }}>

          {/* ── Header row with download buttons ──────────────────────── */}
          <div className="mca-sections-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>
              📈 Pareto Charts
              {vidParsed.set.size > 0 && <span style={{ fontSize: 10, color: '#858585', marginLeft: 6 }}>
                (VID: {vidParsed.multi ? `${vidActiveCount} listed` : [...vidParsed.set][0]})
              </span>}
            </span>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
              <button
                className="btn"
                style={{ fontSize: 11, padding: '2px 8px' }}
                onClick={() => batchDownload('png')}
                title="Download all selected charts as PNG"
              >⬇ PNG</button>
              <button
                className="btn"
                style={{ fontSize: 11, padding: '2px 8px' }}
                onClick={() => batchDownload('jpg')}
                title="Download all selected charts as JPG"
              >⬇ JPG</button>
            </div>
          </div>

          {/* ── Chart selector — grouped by sheet ──────────────────────── */}
          <div style={{ padding: '6px 0 2px', display: 'flex', flexDirection: 'column', gap: 4 }}>

            {/* Overview row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 10, color: '#858585', minWidth: 90 }}>Overview:</span>
              {(() => {
                const sel = selectedCharts.has(CHART_VIEW_TABS);
                return (
                  <button
                    onClick={() => toggleChart(CHART_VIEW_TABS)}
                    style={{
                      fontSize: 11, padding: '2px 10px', borderRadius: 3, border: '1px solid',
                      cursor: 'pointer',
                      background: sel ? '#0e7a0d' : 'transparent',
                      borderColor: sel ? '#0e7a0d' : '#555',
                      color: sel ? '#fff' : 'inherit',
                    }}
                  >Fails per Tab</button>
                );
              })()}
              {(() => {
                const sel = selectedCharts.has(CHART_VIEW_VIDS);
                return (
                  <button
                    onClick={() => toggleChart(CHART_VIEW_VIDS)}
                    style={{
                      fontSize: 11, padding: '2px 10px', borderRadius: 3, border: '1px solid',
                      cursor: 'pointer',
                      background: sel ? '#1a6e4a' : 'transparent',
                      borderColor: sel ? '#1a6e4a' : '#555',
                      color: sel ? '#fff' : 'inherit',
                    }}
                  >Fails per VID</button>
                );
              })()}
              {(() => {
                const sel = selectedCharts.has(CHART_VIEW_HEATMAP);
                return (
                  <button
                    onClick={() => toggleChart(CHART_VIEW_HEATMAP)}
                    style={{
                      fontSize: 11, padding: '2px 10px', borderRadius: 3, border: '1px solid',
                      cursor: 'pointer',
                      background: sel ? '#5a2d82' : 'transparent',
                      borderColor: sel ? '#5a2d82' : '#555',
                      color: sel ? '#fff' : 'inherit',
                    }}
                  >Multi-IP Heatmap</button>
                );
              })()}
            </div>

            {/* Per-sheet rows */}
            {mcaSheets.map(s => {
              const cols = drillData[s] ?? [];
              if (!cols.length) return null;
              return (
                <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 10, color: '#858585', minWidth: 90 }}>{s}:</span>
                  {cols.map(c => {
                    const id  = `${s}::${c.label}`;
                    const sel = selectedCharts.has(id);
                    return (
                      <button
                        key={id}
                        onClick={() => toggleChart(id)}
                        style={{
                          fontSize: 11, padding: '2px 8px', borderRadius: 3, border: '1px solid',
                          cursor: 'pointer',
                          background: sel ? '#1a5fa8' : 'transparent',
                          borderColor: sel ? '#1a5fa8' : '#555',
                          color: sel ? '#fff' : 'inherit',
                        }}
                      >{c.label}</button>
                    );
                  })}
                </div>
              );
            })}
          </div>

          {/* ── Chart display area ─────────────────────────────────────── */}
          <div style={{ padding: '8px 0' }}>
            {mcaSheets.some(s => loadingBusy.has(s)) && (
              <div style={{ fontSize: 11, color: '#858585', marginBottom: 8 }}>⏳ Loading MCA sheet data…</div>
            )}

            {mcaSheets.length === 0 && (
              <div style={{ fontSize: 11, color: '#858585' }}>No MCA sheets detected in this report.</div>
            )}

            {/* Overview / Fails per Tab chart */}
            {selectedCharts.has(CHART_VIEW_TABS) && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: '#d4d4d4' }}>Fails per Tab</span>
                  <button className="btn" style={{ fontSize: 10, padding: '1px 6px' }}
                    onClick={() => downloadChartContainer(chartRefs.current.get(CHART_VIEW_TABS) ?? null, 'mca_fails_per_tab.png', 'png')}
                  >⬇ PNG</button>
                  <button className="btn" style={{ fontSize: 10, padding: '1px 6px' }}
                    onClick={() => downloadChartContainer(chartRefs.current.get(CHART_VIEW_TABS) ?? null, 'mca_fails_per_tab.jpg', 'jpg')}
                  >⬇ JPG</button>
                </div>
                <div ref={el => { if (el) chartRefs.current.set(CHART_VIEW_TABS, el); }}>
                  {paretoData.length > 0
                    ? <SimpleBarChart data={paretoData} />
                    : <div style={{ fontSize: 11, color: '#858585' }}>No data yet — toggle Charts to load sheets.</div>
                  }
                </div>
              </div>
            )}

            {/* Fails per VID chart */}
            {selectedCharts.has(CHART_VIEW_VIDS) && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: '#d4d4d4' }}>
                    Fails per VID {vidFailData.length > 0 && <span style={{ fontWeight: 400, color: '#888' }}>(top {vidFailData.length})</span>}
                  </span>
                  <button className="btn" style={{ fontSize: 10, padding: '1px 6px' }}
                    onClick={() => downloadChartContainer(chartRefs.current.get(CHART_VIEW_VIDS) ?? null, 'mca_fails_per_vid.png', 'png')}
                  >⬇ PNG</button>
                  <button className="btn" style={{ fontSize: 10, padding: '1px 6px' }}
                    onClick={() => downloadChartContainer(chartRefs.current.get(CHART_VIEW_VIDS) ?? null, 'mca_fails_per_vid.jpg', 'jpg')}
                  >⬇ JPG</button>
                </div>
                <div ref={el => { if (el) chartRefs.current.set(CHART_VIEW_VIDS, el); }}>
                  {vidFailData.length > 0
                    ? <SimpleBarChart data={vidFailData} />
                    : <div style={{ fontSize: 11, color: '#858585' }}>No VID data — load MCA sheets first.</div>
                  }
                </div>
              </div>
            )}

            {/* Multi-IP Heatmap */}
            {selectedCharts.has(CHART_VIEW_HEATMAP) && (
              <div style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: '#d4d4d4' }}>
                    Multi-IP Fail Heatmap
                    {heatmapData.vids.length > 0 && (
                      <span style={{ fontWeight: 400, color: '#888' }}>
                        {' '}({heatmapData.vids.length} unit{heatmapData.vids.length !== 1 ? 's' : ''} failing in 2+ tabs)
                      </span>
                    )}
                  </span>
                  <button className="btn" style={{ fontSize: 10, padding: '1px 6px' }}
                    onClick={() => downloadChartContainer(chartRefs.current.get(CHART_VIEW_HEATMAP) ?? null, 'mca_multi_ip_heatmap.png', 'png')}
                  >⬇ PNG</button>
                  <button className="btn" style={{ fontSize: 10, padding: '1px 6px' }}
                    onClick={() => downloadChartContainer(chartRefs.current.get(CHART_VIEW_HEATMAP) ?? null, 'mca_multi_ip_heatmap.jpg', 'jpg')}
                  >⬇ JPG</button>
                </div>
                <div ref={el => { if (el) chartRefs.current.set(CHART_VIEW_HEATMAP, el); }}>
                  {heatmapData.vids.length > 0
                    ? <HeatmapChart vids={heatmapData.vids} sheets={heatmapData.sheets} matrix={heatmapData.matrix} />
                    : <div style={{ fontSize: 11, color: '#858585' }}>No units failing in multiple IP tabs — or sheets not loaded yet.</div>
                  }
                </div>
              </div>
            )}

            {/* Per-sheet grouped charts */}
            {mcaSheets.map(s => {
              const cols = (drillData[s] ?? []).filter(c => selectedCharts.has(`${s}::${c.label}`));
              if (!cols.length) return null;
              return (
                <div key={s} style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: 12, color: '#aaaaaa', fontWeight: 600, borderBottom: '1px solid #333', paddingBottom: 3, marginBottom: 8 }}>
                    {s}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
                    {cols.map(c => {
                      const id   = `${s}::${c.label}`;
                      const safe = id.replace('::', '_').replace(/[^a-zA-Z0-9_-]/g, '_');
                      return (
                        <div key={id} style={{ minWidth: 320 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                            <span
                              data-chart-title="1"
                              style={{ fontSize: 11, color: '#858585' }}
                            >{c.label} <span style={{ color: '#666' }}>({c.colName})</span></span>
                            <button
                              className="btn"
                              style={{ fontSize: 10, padding: '1px 6px' }}
                              onClick={() => downloadChartContainer(chartRefs.current.get(id) ?? null, `${safe}.png`, 'png')}
                            >⬇ PNG</button>
                            <button
                              className="btn"
                              style={{ fontSize: 10, padding: '1px 6px' }}
                              onClick={() => downloadChartContainer(chartRefs.current.get(id) ?? null, `${safe}.jpg`, 'jpg')}
                            >⬇ JPG</button>
                          </div>
                          <div ref={el => { if (el) chartRefs.current.set(id, el); }}>
                            <SimpleBarChart data={c.entries} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
