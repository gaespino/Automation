/**
 * MCAPreview — structured inline viewer for a generated MCA report.
 *
 * Features:
 *   • VID filter — text box that filters rows across ALL tables simultaneously
 *   • Analysis sheet auto-split into collapsible sections:
 *       Root Cause  (VID, Runs, WW, Root Cause, Debug Hunts, Failing Area …)
 *       CHA / CORE / MEM / IO / OTHERS  (per-IP columns)
 *   • Optional MCA data tables (CHA_MCAs, CORE_MCAs, etc.) — checkboxes, off by default
 *   • Optional Pareto chart — shows failing-instance count per MCA tab, off by default
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
  if (ROOT_PATTERNS.some(r => r.test(col))) return '__root';
  for (const g of IP_GROUPS) {
    if (g.pats.some(p => p.test(col))) return g.id;
  }
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

const PAGE = 300;

// ---------------------------------------------------------------------------
// Mini table for a subset of columns from a full SheetData
// ---------------------------------------------------------------------------
function SectionTable({
  allCols, colIdxs, rows, vidFilter, vidIdx,
}: {
  allCols: string[];
  colIdxs: number[];
  rows: (string | number | null)[][];
  vidFilter: string;
  vidIdx: number;
}) {
  const low = vidFilter.trim().toLowerCase();
  const filtered = useMemo(() => {
    if (!low || vidIdx < 0) return rows;
    return rows.filter(r => String(r[vidIdx] ?? '').toLowerCase().includes(low));
  }, [rows, low, vidIdx]);

  if (!colIdxs.length) {
    return <span style={{ color: '#858585', fontSize: 11 }}>No matching columns.</span>;
  }

  const shown = filtered.slice(0, PAGE);

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="ev-table" style={{ fontSize: 11 }}>
        <thead>
          <tr>
            {colIdxs.map(i => (
              <th key={i} style={{ padding: '4px 8px', whiteSpace: 'nowrap' }}>{allCols[i]}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((row, ri) => (
            <tr key={ri} className={ri % 2 === 1 ? 'ev-row-alt' : ''}>
              {colIdxs.map(ci => (
                <td key={ci} style={{ padding: '3px 8px', whiteSpace: 'nowrap', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {String(row[ci] ?? '')}
                </td>
              ))}
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
// Main component
// ---------------------------------------------------------------------------
export default function MCAPreview({ token, apiBase }: Props) {
  const [allSheets,    setAllSheets]    = useState<string[]>([]);
  const [analysisData, setAnalysisData] = useState<SheetData | null>(null);
  const [mcaData,      setMcaData]      = useState<Record<string, SheetData>>({});
  const [loadingBusy,  setLoadingBusy]  = useState<Set<string>>(new Set());

  // UI state
  const [vidFilter,   setVidFilter]   = useState('');
  const [showMcaTabs, setShowMcaTabs] = useState<Record<string, boolean>>({});
  const [showCharts,  setShowCharts]  = useState(false);
  const [collapsed,   setCollapsed]   = useState<Set<string>>(new Set());
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
    () => allSheets.find(s => /^analysis$/i.test(s)) ?? '',
    [allSheets],
  );
  const mcaSheets = useMemo(() => allSheets.filter(isMcaSheet), [allSheets]);

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

  // VID-filtered rows for analysis
  const anaRows = useMemo(() => {
    if (!analysisData) return [];
    const low = vidFilter.trim().toLowerCase();
    if (!low || vidIdx < 0) return analysisData.rows;
    return analysisData.rows.filter(r => String(r[vidIdx] ?? '').toLowerCase().includes(low));
  }, [analysisData, vidFilter, vidIdx]);

  // VID-filtered rows for a given MCA sheet
  const mcaRows = useCallback((sheet: string) => {
    const d = mcaData[sheet];
    if (!d) return [];
    const low = vidFilter.trim().toLowerCase();
    if (!low) return d.rows;
    const vi = findVidCol(d.columns);
    if (vi < 0) return d.rows;
    return d.rows.filter(r => String(r[vi] ?? '').toLowerCase().includes(low));
  }, [mcaData, vidFilter]);

  const toggleSection = (id: string) =>
    setCollapsed(s => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  // Pareto data: rows per MCA sheet (with VID filter)
  const paretoData = useMemo<BarEntry[]>(() => {
    return mcaSheets
      .filter(s => mcaData[s])
      .map(s => ({ label: s, value: mcaRows(s).length }))
      .sort((a, b) => b.value - a.value);
  }, [mcaSheets, mcaData, mcaRows]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  if (!token) return null;
  if (error)  return <div className="ev-error">{error}</div>;

  // Ordered analysis sections
  const sectionOrder: Array<{ id: string; icon: string; label: string }> = [
    { id: '__root', icon: '🔍', label: 'Root Cause' },
    ...IP_GROUPS.map(g => ({ id: g.id, icon: g.icon, label: g.label })),
    { id: 'OTHERS', icon: '📦', label: 'Others' },
  ];

  return (
    <div className="mca-preview">

      {/* ── Controls bar ─────────────────────────────────────────────────── */}
      <div className="mca-preview-controls">
        <div className="mca-preview-vid-row">
          <span style={{ fontSize: 11, color: '#858585', whiteSpace: 'nowrap' }}>🔍 Filter VID:</span>
          <input
            value={vidFilter}
            onChange={e => setVidFilter(e.target.value)}
            placeholder="Type VID to filter all tables…"
            style={{ flex: 1, minWidth: 180, fontSize: 12 }}
          />
          {vidFilter && (
            <button className="btn" style={{ padding: '2px 8px' }} onClick={() => setVidFilter('')}>✕</button>
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
          <label className="check-label" style={{ fontSize: 11, marginLeft: 'auto' }}>
            <input type="checkbox" checked={showCharts} onChange={() => setShowCharts(v => !v)} />
            📊 Charts
          </label>
        </div>
      </div>

      {/* ── Analysis section ─────────────────────────────────────────────── */}
      {loadingAna && (
        <div style={{ padding: 12, color: '#858585', fontSize: 12 }}>⏳ Loading Analysis sheet…</div>
      )}

      {analysisData && !loadingAna && (
        <div className="mca-sections">
          <div className="mca-sections-title">📊 Analysis — {anaRows.length} rows{vidFilter ? ` (filtered)` : ''}</div>

          {sectionOrder.map(({ id, icon, label }) => {
            const idxs = analysisGroups?.[id] ?? [];
            if (!idxs.length) return null;
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
                  colIdxs={idxs}
                  rows={analysisData.rows}
                  vidFilter={vidFilter}
                  vidIdx={vidIdx}
                />
              </Section>
            );
          })}

          {(analysisGroups && Object.values(analysisGroups).every(a => !a.length)) && (
            <div style={{ fontSize: 11, color: '#858585', padding: 8 }}>
              Loaded {analysisData.total_rows} rows × {analysisData.columns.length} columns.
              Column names did not match known IP patterns — showing raw view.
            </div>
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
                    vidFilter={vidFilter}
                    vidIdx={findVidCol(d.columns)}
                  />
                )}
              </Section>
            );
          })}
        </div>
      )}

      {/* ── Pareto chart ─────────────────────────────────────────────────── */}
      {showCharts && (
        <div className="mca-sections" style={{ marginTop: 10 }}>
          <div className="mca-sections-title">
            📈 Pareto — Failing Instances per MCA Tab
            {vidFilter && <span style={{ fontSize: 10, color: '#858585', marginLeft: 6 }}>
              (VID filter: {vidFilter})
            </span>}
          </div>
          <div style={{ padding: '8px 0' }}>
            {mcaSheets.some(s => loadingBusy.has(s)) && (
              <div style={{ fontSize: 11, color: '#858585', marginBottom: 8 }}>⏳ Loading MCA sheet data…</div>
            )}
            {paretoData.length > 0 ? (
              <SimpleBarChart data={paretoData} />
            ) : mcaSheets.length === 0 ? (
              <div style={{ fontSize: 11, color: '#858585' }}>No MCA sheets detected in this report.</div>
            ) : (
              <div style={{ fontSize: 11, color: '#858585' }}>
                {mcaSheets.every(s => loadingBusy.has(s))
                  ? 'Loading…'
                  : 'No data loaded yet — MCA sheets will be fetched automatically.'}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
