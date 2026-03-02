import React, { useState, useEffect, useMemo, useRef } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';
const PAGE_SIZE = 200;
const ALL_COLS = ['IP_Origin', 'ip_name', 'Instance', 'description', 'Default', 'Group', 'Bits'] as const;
type Col = typeof ALL_COLS[number];

const DEFAULT_VISIBLE: Set<Col> = new Set(['IP_Origin', 'ip_name', 'Instance', 'description']);

const SOCKET_OPTIONS = [
  { label: 'All Sockets', value: 'sockets' },
  { label: 'Socket 0',    value: 'socket0' },
  { label: 'Socket 1',    value: 'socket1' },
];

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

interface Fuse {
  Name: string;         // original_name – unique key, not shown in table
  IP_Origin: string;    // uppercase filename (COMPUTE, IO, …)
  ip_name: string;      // ip_name column from CSV
  Instance: string;     // Instance column from CSV
  description: string;
  Default: string;
  Group: string;
  Bits: string;
}
interface IPTarget { label: string; value: string; }

// ── Generate Modal ────────────────────────────────────────────────────────────
function GenerateModal({ product, selected, fuses, filename, onClose }: {
  product: string; selected: Set<string>; fuses: Fuse[]; filename: string; onClose: () => void;
}) {
  const [targets,    setTargets]    = useState<IPTarget[]>([]);
  const [checkedIPs, setCheckedIPs] = useState<Set<string>>(new Set());
  const [checkedSks, setCheckedSks] = useState<Set<string>>(new Set(['sockets']));
  const [values,     setValues]     = useState<Record<string, string>>({});
  const [outFile,    setOutFile]    = useState(filename);
  const [generating, setGenerating] = useState(false);
  const [error,      setError]      = useState('');

  const selectedFuses = useMemo(() => fuses.filter(f => selected.has(f.Name)), [fuses, selected]);

  useEffect(() => {
    fetch(`${BASE}/fuses/${product}/ip-targets`)
      .then(r => r.json()).then(d => setTargets(d.targets ?? [])).catch(() => setTargets([]));
    const v: Record<string, string> = {};
    selectedFuses.forEach(f => { v[f.Name] = f.Default || '0'; });
    setValues(v);
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const toggleIP = (val: string) =>
    setCheckedIPs(s => { const n = new Set(s); n.has(val) ? n.delete(val) : n.add(val); return n; });
  const toggleSk = (val: string) =>
    setCheckedSks(s => { const n = new Set(s); n.has(val) ? n.delete(val) : n.add(val); return n; });

  const handleGenerate = async () => {
    if (!checkedIPs.size) { setError('Select at least one IP target.'); return; }
    if (!checkedSks.size) { setError('Select at least one socket.'); return; }
    setGenerating(true); setError('');
    try {
      const resp = await fetch(`${BASE}/fuses/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product,
          selected_names: [...selected],
          fuse_values: values,
          ip_targets: [...checkedIPs],
          sockets: [...checkedSks],
          filename: outFile,
        }),
      });
      if (!resp.ok) { setError(`${resp.status}: ${await resp.text()}`); }
      else {
        const blob = await resp.blob();
        const cd   = resp.headers.get('content-disposition') ?? '';
        const m    = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fn   = m ? m[1].replace(/['"]/g, '') : `${outFile}.fuse`;
        downloadBlob(blob, fn);
        onClose();
      }
    } catch (e: unknown) { setError((e as Error).message); }
    finally { setGenerating(false); }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        <div className="modal-header">
          <span>🔌 Generate Fuse File &mdash; {selected.size} fuses selected</span>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-section">
          <div className="modal-section-title">Step 1 — Sockets</div>
          <div className="ip-target-grid">
            {SOCKET_OPTIONS.map(s => (
              <label key={s.value} className="ip-target-item">
                <input type="checkbox" checked={checkedSks.has(s.value)} onChange={() => toggleSk(s.value)} />
                {s.label}
              </label>
            ))}
          </div>
        </div>

        <div className="modal-section">
          <div className="modal-section-title">Step 2 — IP Targets <span className="muted">(sections written in the .fuse file)</span></div>
          {targets.length === 0
            ? <span className="muted">No targets available for {product}.</span>
            : <div className="ip-target-grid">
                {targets.map(t => (
                  <label key={t.value} className="ip-target-item">
                    <input type="checkbox" checked={checkedIPs.has(t.value)} onChange={() => toggleIP(t.value)} />
                    {t.label}
                  </label>
                ))}
              </div>
          }
        </div>

        <div className="modal-section">
          <div className="modal-section-title">
            Fuse Values <span className="muted">(key = ip_name.instance; edit to override default)</span>
          </div>
          <div className="fuse-values-table">
            <div className="fuse-value-row fuse-value-header">
              <span>ip_name.Instance</span>
              <span>Group</span>
              <span>Bits</span>
              <span>Default</span>
              <span>Value</span>
            </div>
            {selectedFuses.map(f => (
              <div key={f.Name} className="fuse-value-row">
                <span className="fv-name" title={f.Name}>{f.ip_name}.{f.Instance}</span>
                <span className="fv-group">{f.Group}</span>
                <span className="fv-bits">{f.Bits ? `${f.Bits}b` : '—'}</span>
                <span className="fv-default">{f.Default || '—'}</span>
                <input className="fv-input"
                  value={values[f.Name] ?? f.Default ?? '0'}
                  onChange={e => setValues(v => ({ ...v, [f.Name]: e.target.value }))} />
              </div>
            ))}
          </div>
        </div>

        <div className="modal-section" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label style={{ color: '#858585', fontSize: 12, whiteSpace: 'nowrap' }}>Output filename:</label>
          <input className="fv-input" style={{ flex: 1 }}
            value={outFile} onChange={e => setOutFile(e.target.value)} placeholder="fuses_output" />
        </div>

        {error && <div className="error-msg" style={{ margin: '0 0 8px' }}>{error}</div>}
        <div className="modal-footer">
          <button className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" onClick={handleGenerate} disabled={generating || !checkedIPs.size || !checkedSks.size}>
            {generating ? '⏳ Generating…' : '⬇ Generate & Download'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Column Visibility Popover ─────────────────────────────────────────────────
function ColVisibility({ visible, onChange }: {
  visible: Set<Col>; onChange: (c: Set<Col>) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const toggle = (c: Col) => {
    const n = new Set(visible);
    n.has(c) ? n.delete(c) : n.add(c);
    onChange(n);
  };

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button className="btn" onClick={() => setOpen(o => !o)} style={{ fontSize: 11 }}>
        Columns ▾
      </button>
      {open && (
        <div className="col-vis-popup">
          {ALL_COLS.map(c => (
            <label key={c} className="col-vis-item">
              <input type="checkbox" checked={visible.has(c)} onChange={() => toggle(c)} /> {c}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Helper: compile a user-typed string as regex (fall back to literal match) ──
function tryRegex(pattern: string): RegExp | null {
  if (!pattern) return null;
  try { return new RegExp(pattern, 'i'); }
  catch (_e) { return new RegExp(pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i'); }
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function FuseGenerator() {
  const [product,    setProduct]    = useState('GNR');
  const [fuses,      setFuses]      = useState<Fuse[]>([]);
  const [filterIpOrigin, setFilterIpOrigin] = useState('');
  const [filterIpName,   setFilterIpName]   = useState('');
  const [filterInstance, setFilterInstance] = useState('');
  const [filterDesc,     setFilterDesc]     = useState('');
  const [selected,   setSelected]   = useState<Set<string>>(new Set());
  const [filename,   setFilename]   = useState('fuses_output');
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState('');
  const [page,       setPage]       = useState(1);
  const [showModal,  setShowModal]  = useState(false);
  const [visibleCols, setVisibleCols] = useState<Set<Col>>(new Set(DEFAULT_VISIBLE));

  useEffect(() => {
    setLoading(true); setError(''); setFuses([]); setSelected(new Set());
    setFilterIpOrigin(''); setFilterIpName(''); setFilterInstance(''); setFilterDesc('');
    fetch(`${BASE}/fuses/${product}`)
      .then(r => { if (!r.ok) throw new Error(`Fuses: ${r.status}`); return r.json(); })
      .then(d  => setFuses(d.fuses ?? []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [product]);

  useEffect(() => { setPage(1); }, [filterIpOrigin, filterIpName, filterInstance, filterDesc, fuses]);

  const filtered = useMemo(() => {
    const rOrg  = tryRegex(filterIpOrigin);
    const rName = tryRegex(filterIpName);
    const rInst = tryRegex(filterInstance);
    const rDesc = tryRegex(filterDesc);
    return fuses.filter(f =>
      (!rOrg  || rOrg.test(f.IP_Origin))   &&
      (!rName || rName.test(f.ip_name))     &&
      (!rInst || rInst.test(f.Instance))    &&
      (!rDesc || rDesc.test(f.description))
    );
  }, [fuses, filterIpOrigin, filterIpName, filterInstance, filterDesc]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated  = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const toggle        = (name: string) =>
    setSelected(s => { const n = new Set(s); n.has(name) ? n.delete(name) : n.add(name); return n; });
  const selectAll      = () => setSelected(new Set(fuses.map(f => f.Name)));
  const clearAll       = () => setSelected(new Set());
  const selectFiltered = () => setSelected(s => { const n = new Set(s); filtered.forEach(f => n.add(f.Name)); return n; });
  const clearFiltered  = () => setSelected(s => { const n = new Set(s); filtered.forEach(f => n.delete(f.Name)); return n; });

  const colCount = 1 + ALL_COLS.filter(c => visibleCols.has(c)).length;

  return (
    <div className="tool-page">
      <h2 className="page-title">🔌 Fuse Generator</h2>

      {showModal && (
        <GenerateModal
          product={product} selected={selected} fuses={fuses}
          filename={filename} onClose={() => setShowModal(false)} />
      )}

      <div className="fg-top-row">
        <div className="panel fg-controls">
          <div className="section-title">Filters</div>
          <div className="form-grid">
            <label>Product</label>
            <select value={product} onChange={e => setProduct(e.target.value)}>
              {['GNR', 'CWF', 'DMR'].map(p => <option key={p}>{p}</option>)}
            </select>

            <label>IP Origin</label>
            <input value={filterIpOrigin} onChange={e => setFilterIpOrigin(e.target.value)}
              placeholder="regex e.g. COMPUTE" />

            <label>IP Name</label>
            <input value={filterIpName} onChange={e => setFilterIpName(e.target.value)}
              placeholder="regex e.g. bgr_c01" />

            <label>Instance</label>
            <input value={filterInstance} onChange={e => setFilterInstance(e.target.value)}
              placeholder="regex e.g. trim_en" />

            <label>Description</label>
            <input value={filterDesc} onChange={e => setFilterDesc(e.target.value)}
              placeholder="regex e.g. voltage" />

            <label>Output File</label>
            <input value={filename} onChange={e => setFilename(e.target.value)}
              placeholder="fuses_output" />
          </div>
        </div>

        <div className="panel fg-actions">
          <div className="section-title">Selection</div>
          <div className="fg-btn-grid">
            <button className="btn" onClick={selectAll}>☑ All</button>
            <button className="btn" onClick={clearAll}>☐ None</button>
            <button className="btn" onClick={selectFiltered}>☑ Filtered</button>
            <button className="btn" onClick={clearFiltered}>☐ Filtered</button>
          </div>
          <div className="fuse-badge" style={{ marginTop: 10 }}>
            <span className="badge">{selected.size}</span> selected &nbsp;·&nbsp;{' '}
            <span className="badge-dim">{fuses.length.toLocaleString()}</span> total
            {' '}(<span className="badge-dim">{filtered.length.toLocaleString()}</span> matching)
          </div>
          {error && <div className="error-msg" style={{ marginTop: 8 }}>{error}</div>}
          <div style={{ marginTop: 12 }}>
            <button
              className="btn primary"
              onClick={() => { if (!selected.size) { setError('No fuses selected.'); return; } setError(''); setShowModal(true); }}
              disabled={!selected.size}
              style={{ width: '100%' }}
            >
              ▶ Generate Fuse File…
            </button>
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 12 }}>
        <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>Fuses {loading && <span className="loading-badge">Loading…</span>}</span>
          <span style={{ flex: 1 }} />
          <ColVisibility visible={visibleCols} onChange={setVisibleCols} />
        </div>
        <div className="fuse-table-wrap">
          <table className="fuse-table">
            <thead>
              <tr>
                <th>
                  <input type="checkbox"
                    checked={paginated.length > 0 && paginated.every(f => selected.has(f.Name))}
                    onChange={e => {
                      const n = new Set(selected);
                      paginated.forEach(f => e.target.checked ? n.add(f.Name) : n.delete(f.Name));
                      setSelected(n);
                    }} />
                </th>
                {visibleCols.has('IP_Origin')   && <th>IP Origin</th>}
                {visibleCols.has('ip_name')     && <th>IP Name</th>}
                {visibleCols.has('Instance')    && <th>Instance</th>}
                {visibleCols.has('description') && <th>Description</th>}
                {visibleCols.has('Default')     && <th>Default</th>}
                {visibleCols.has('Group')       && <th>Group</th>}
                {visibleCols.has('Bits')        && <th>Bits</th>}
              </tr>
            </thead>
            <tbody>
              {paginated.map(f => (
                <tr key={f.Name} className={selected.has(f.Name) ? 'row-selected' : ''}>
                  <td><input type="checkbox" checked={selected.has(f.Name)} onChange={() => toggle(f.Name)} /></td>
                  {visibleCols.has('IP_Origin')   && <td className="fuse-ip">{f.IP_Origin}</td>}
                  {visibleCols.has('ip_name')     && <td className="fuse-ipname">{f.ip_name}</td>}
                  {visibleCols.has('Instance')    && <td className="fuse-name">{f.Instance}</td>}
                  {visibleCols.has('description') && <td className="fuse-desc">{f.description}</td>}
                  {visibleCols.has('Default')     && <td className="fuse-def">{f.Default}</td>}
                  {visibleCols.has('Group')       && <td className="fuse-grp">{f.Group}</td>}
                  {visibleCols.has('Bits')        && <td className="fuse-bits">{f.Bits}</td>}
                </tr>
              ))}
              {!loading && filtered.length === 0 && (
                <tr><td colSpan={colCount} style={{ textAlign: 'center', color: '#858585', padding: 16 }}>
                  {fuses.length === 0 ? 'No fuses loaded.' : 'No fuses match filter.'}
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div className="fg-pagination">
            <button className="btn" onClick={() => setPage(1)} disabled={page === 1}>«</button>
            <button className="btn" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>‹</button>
            <span className="pg-info">
              Page {page} / {totalPages} &nbsp;·&nbsp; showing {((page-1)*PAGE_SIZE+1).toLocaleString()}–{Math.min(page*PAGE_SIZE, filtered.length).toLocaleString()} of {filtered.length.toLocaleString()} filtered rows
            </span>
            <button className="btn" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>›</button>
            <button className="btn" onClick={() => setPage(totalPages)} disabled={page === totalPages}>»</button>
          </div>
        )}
      </div>
    </div>
  );
}
