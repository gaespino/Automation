/**
 * ExcelViewer — renders a tabbed, filterable view of an Excel report
 * fetched from a backend `/sheet_data` endpoint.
 *
 * Props:
 *   token       — server-side cache token returned with the report response
 *   apiBase     — base path for sheet API, e.g. '/api/framework' or '/api/mca'
 *   sheetFilter — optional predicate to include only certain tab names
 */
import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import './ExcelViewer.css';

interface SheetData {
  sheet: string;
  columns: string[];
  rows: (string | number | null)[][];
  total_rows: number;
}

interface Props {
  token: string;
  apiBase: string;
  sheetFilter?: (name: string) => boolean;
}

const PAGE_SIZE = 300;
const MIN_COL_W = 40;
const DEF_COL_W = 120;

export default function ExcelViewer({ token, apiBase, sheetFilter }: Props) {
  const [allSheets,   setAllSheets]   = useState<string[]>([]);
  const [active,      setActive]      = useState('');
  const [data,        setData]        = useState<SheetData | null>(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState('');
  const [filters,     setFilters]     = useState<Record<string, string>>({});
  const [page,        setPage]        = useState(0);
  const [hiddenCols,  setHiddenCols]  = useState<Set<string>>(new Set());
  const [colWidths,   setColWidths]   = useState<Record<string, number>>({});
  const [showColPanel, setShowColPanel] = useState(false);

  // drag-resize state
  const dragRef = useRef<{ col: string; startX: number; startW: number } | null>(null);

  const startResize = useCallback((e: React.MouseEvent, col: string) => {
    e.preventDefault();
    const startW = colWidths[col] ?? DEF_COL_W;
    dragRef.current = { col, startX: e.clientX, startW };

    const onMove = (ev: MouseEvent) => {
      if (!dragRef.current) return;
      const delta = ev.clientX - dragRef.current.startX;
      const newW  = Math.max(MIN_COL_W, dragRef.current.startW + delta);
      setColWidths(w => ({ ...w, [dragRef.current!.col]: newW }));
    };
    const onUp = () => {
      dragRef.current = null;
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup',   onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup',   onUp);
  }, [colWidths]);

  // Load sheet list when token changes
  useEffect(() => {
    if (!token) return;
    setError('');
    fetch(`${apiBase}/sheets?token=${encodeURIComponent(token)}`)
      .then(r => r.json())
      .then(d => {
        const names: string[] = [];
        Object.values(d as Record<string, string[]>).forEach(arr => {
          if (Array.isArray(arr)) arr.forEach(n => { if (!names.includes(n)) names.push(n); });
        });
        const visible = sheetFilter ? names.filter(sheetFilter) : names;
        setAllSheets(visible);
        setActive(visible[0] ?? '');
      })
      .catch(e => setError(`Failed to load sheets: ${e.message}`));
  }, [token, apiBase]);

  // Load sheet data when active tab changes
  useEffect(() => {
    if (!active || !token) return;
    setLoading(true); setData(null); setFilters({}); setPage(0); setHiddenCols(new Set()); setColWidths({});
    fetch(`${apiBase}/sheet_data?token=${encodeURIComponent(token)}&sheet=${encodeURIComponent(active)}`)
      .then(r => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then(d => setData(d))
      .catch(e => setError(`Failed to load sheet "${active}": ${e.message}`))
      .finally(() => setLoading(false));
  }, [active, token, apiBase]);

  const visibleCols = useMemo(() => {
    if (!data) return [];
    return data.columns.filter(c => !hiddenCols.has(c));
  }, [data, hiddenCols]);

  const visibleIdxs = useMemo(() => {
    if (!data) return [];
    return data.columns.map((c, i) => ({ c, i })).filter(({ c }) => !hiddenCols.has(c)).map(({ i }) => i);
  }, [data, hiddenCols]);

  const filtered = useMemo(() => {
    if (!data) return [];
    const hasFilter = Object.values(filters).some(Boolean);
    if (!hasFilter) return data.rows;
    return data.rows.filter(row =>
      Object.entries(filters).every(([col, val]) => {
        if (!val) return true;
        const idx = data.columns.indexOf(col);
        if (idx < 0) return true;
        return String(row[idx] ?? '').toLowerCase().includes(val.toLowerCase());
      })
    );
  }, [data, filters]);

  const paged      = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

  const setFilter = (col: string, val: string) => {
    setFilters(f => ({ ...f, [col]: val }));
    setPage(0);
  };

  const toggleCol = (col: string) =>
    setHiddenCols(prev => {
      const next = new Set(prev);
      next.has(col) ? next.delete(col) : next.add(col);
      return next;
    });

  const showAll  = () => setHiddenCols(new Set());
  const hideAll  = () => setHiddenCols(new Set(data?.columns ?? []));

  if (!token) return null;
  if (error)  return <div className="ev-error">{error}</div>;
  if (allSheets.length === 0 && !loading) return null;

  return (
    <div className="ev-container">
      {/* Tab bar */}
      <div className="ev-tabs">
        {allSheets.map(s => (
          <button
            key={s}
            className={`ev-tab${s === active ? ' active' : ''}`}
            onClick={() => { setActive(s); setShowColPanel(false); }}
          >{s}</button>
        ))}
      </div>

      {loading && <div className="ev-loading">⏳ Loading…</div>}

      {data && !loading && (
        <>
          {/* Meta / toolbar */}
          <div className="ev-meta">
            <span className="ev-meta-count">
              {filtered.length !== data.total_rows
                ? `${filtered.length} / ${data.total_rows} rows (filtered)`
                : `${data.total_rows} rows`}
              {hiddenCols.size > 0 && ` · ${hiddenCols.size} column${hiddenCols.size > 1 ? 's' : ''} hidden`}
            </span>
            {Object.values(filters).some(Boolean) && (
              <button className="ev-clear-btn" onClick={() => { setFilters({}); setPage(0); }}>
                ✕ Clear filters
              </button>
            )}
            <button
              className={`ev-tool-btn${showColPanel ? ' active' : ''}`}
              title="Show/hide columns"
              onClick={() => setShowColPanel(v => !v)}
            >⊞ Columns</button>
          </div>

          {/* Column selector panel */}
          {showColPanel && (
            <div className="ev-col-panel">
              <div className="ev-col-panel-actions">
                <button className="ev-clear-btn" onClick={showAll}>Show all</button>
                <button className="ev-clear-btn" onClick={hideAll}>Hide all</button>
              </div>
              <div className="ev-col-checkboxes">
                {data.columns.map(col => (
                  <label key={col} className="ev-col-check">
                    <input
                      type="checkbox"
                      checked={!hiddenCols.has(col)}
                      onChange={() => toggleCol(col)}
                    />
                    <span title={col}>{col}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="ev-table-wrap">
            <table className="ev-table">
              <colgroup>
                {visibleCols.map(col => (
                  <col key={col} style={{ width: colWidths[col] ?? DEF_COL_W }} />
                ))}
              </colgroup>
              <thead>
                <tr>
                  {visibleCols.map(col => (
                    <th key={col} style={{ width: colWidths[col] ?? DEF_COL_W, position: 'relative' }}>
                      <div className="ev-col-name" title={col}>{col}</div>
                      <input
                        className="ev-filter-input"
                        placeholder="filter…"
                        value={filters[col] ?? ''}
                        onChange={e => setFilter(col, e.target.value)}
                      />
                      {/* Resize handle */}
                      <div
                        className="ev-resize-handle"
                        onMouseDown={e => startResize(e, col)}
                      />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paged.map((row, i) => (
                  <tr key={i} className={i % 2 ? 'ev-row-alt' : ''}>
                    {visibleIdxs.map(j => (
                      <td key={j} title={row[j] == null ? '' : String(row[j])}>
                        {row[j] == null ? '' : String(row[j])}
                      </td>
                    ))}
                  </tr>
                ))}
                {paged.length === 0 && (
                  <tr><td colSpan={visibleCols.length} className="ev-empty">No rows match the current filters.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="ev-pagination">
              <button className="ev-pg-btn" disabled={page === 0} onClick={() => setPage(0)}>⏮</button>
              <button className="ev-pg-btn" disabled={page === 0} onClick={() => setPage(p => p - 1)}>◀</button>
              <span className="ev-pg-info">Page {page + 1} / {totalPages}</span>
              <button className="ev-pg-btn" disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}>▶</button>
              <button className="ev-pg-btn" disabled={page >= totalPages - 1} onClick={() => setPage(totalPages - 1)}>⏭</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
