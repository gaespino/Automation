import React, { useState, useEffect, useMemo, useRef } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';
const PAGE_SIZE = 200;
const ALL_COLS = ['Name', 'IP', 'Description', 'Bits', 'Default', 'Group'] as const;
type Col = typeof ALL_COLS[number];

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

interface Fuse { Name: string; IP: string; Description: string; Bits: string; Default: string; Group: string; }
interface IPTarget { label: string; value: string; }

// ── Generate Modal ────────────────────────────────────────────────────────────
function GenerateModal({ product, selected, fuses, filename, onClose }: {
  product: string; selected: Set<string>; fuses: Fuse[]; filename: string; onClose: () => void;
}) {
  const [targets,     setTargets]     = useState<IPTarget[]>([]);
  const [checked,     setChecked]     = useState<Set<string>>(new Set());
  const [values,      setValues]      = useState<Record<string, string>>({});
  const [outFile,     setOutFile]     = useState(filename);
  const [generating,  setGenerating]  = useState(false);
  const [error,       setError]       = useState('');

  const selectedFuses = useMemo(() => fuses.filter(f => selected.has(f.Name)), [fuses, selected]);

  useEffect(() => {
    fetch(`${BASE}/fuses/${product}/ip-targets`)
      .then(r => r.json()).then(d => setTargets(d.targets ?? [])).catch(() => setTargets([]));
    const v: Record<string, string> = {};
    selectedFuses.forEach(f => { v[f.Name] = f.Default || '0'; });
    setValues(v);
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const toggleTarget = (val: string) =>
    setChecked(s => { const n = new Set(s); n.has(val) ? n.delete(val) : n.add(val); return n; });

  const handleGenerate = async () => {
    if (!checked.size) { setError('Select at least one IP target.'); return; }
    setGenerating(true); setError('');
    try {
      const resp = await fetch(`${BASE}/fuses/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product,
          selected_names: [...selected],
          fuse_values: values,
          ip_targets: [...checked],
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
          <div className="modal-section-title">IP Targets <span className="muted">(select sections to write in the .fuse file)</span></div>
          {targets.length === 0
            ? <span className="muted">No targets available for {product}.</span>
            : <div className="ip-target-grid">
                {targets.map(t => (
                  <label key={t.value} className="ip-target-item">
                    <input type="checkbox" checked={checked.has(t.value)} onChange={() => toggleTarget(t.value)} />
                    {t.label}
                  </label>
                ))}
              </div>
          }
        </div>

        <div className="modal-section">
          <div className="modal-section-title">
            Fuse Values <span className="muted">(pre-filled from Default column; edit to override)</span>
          </div>
          <div className="fuse-values-table">
            {selectedFuses.map(f => (
              <div key={f.Name} className="fuse-value-row">
                <span className="fv-name">{f.Name}</span>
                <span className="fv-bits">{f.Bits ? `${f.Bits}b` : ''}</span>
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
          <button className="btn primary" onClick={handleGenerate} disabled={generating || !checked.size}>
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

// ── Main Component ────────────────────────────────────────────────────────────
export default function FuseGenerator() {
  const [product,     setProduct]     = useState('GNR');
  const [fuses,       setFuses]       = useState<Fuse[]>([]);
  const [ips,         setIps]         = useState<string[]>([]);
  const [groups,      setGroups]      = useState<string[]>([]);
  const [search,      setSearch]      = useState('');
  const [filterIp,    setFilterIp]    = useState('');
  const [filterGrp,   setFilterGrp]   = useState('');
  const [filterBits,  setFilterBits]  = useState('');
  const [selected,    setSelected]    = useState<Set<string>>(new Set());
  const [filename,    setFilename]    = useState('fuses_output');
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState('');
  const [page,        setPage]        = useState(1);
  const [showModal,   setShowModal]   = useState(false);
  const [visibleCols, setVisibleCols] = useState<Set<Col>>(new Set(ALL_COLS));

  useEffect(() => {
    setLoading(true); setError(''); setFuses([]); setSelected(new Set());
    setFilterIp(''); setFilterGrp(''); setFilterBits(''); setSearch('');
    Promise.all([
      fetch(`${BASE}/fuses/${product}`).then(r => { if (!r.ok) throw new Error(`Fuses: ${r.status}`); return r.json(); }),
      fetch(`${BASE}/fuses/${product}/metadata`).then(r => { if (!r.ok) throw new Error(`Metadata: ${r.status}`); return r.json(); }),
    ]).then(([fusesData, meta]) => {
      setFuses(fusesData.fuses ?? []);
      setIps(meta.ips ?? []);
      setGroups(meta.groups ?? []);
    }).catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [product]);

  useEffect(() => { setPage(1); }, [search, filterIp, filterGrp, filterBits, fuses]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return fuses.filter(f =>
      (!q || f.Name.toLowerCase().includes(q) || f.Description.toLowerCase().includes(q) ||
             f.IP.toLowerCase().includes(q)   || f.Group.toLowerCase().includes(q)       ||
             f.Bits.toLowerCase().includes(q) || f.Default.toLowerCase().includes(q))    &&
      (!filterIp   || f.IP === filterIp)       &&
      (!filterGrp  || f.Group === filterGrp)   &&
      (!filterBits || f.Bits === filterBits)
    );
  }, [fuses, search, filterIp, filterGrp, filterBits]);

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

            <label>Search</label>
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search all columns…" />

            <label>IP</label>
            <select value={filterIp} onChange={e => setFilterIp(e.target.value)}>
              <option value="">All IPs</option>
              {ips.map(ip => <option key={ip}>{ip}</option>)}
            </select>

            <label>Group</label>
            <select value={filterGrp} onChange={e => setFilterGrp(e.target.value)}>
              <option value="">All Groups</option>
              {groups.map(g => <option key={g}>{g}</option>)}
            </select>

            <label>Bits</label>
            <input value={filterBits} onChange={e => setFilterBits(e.target.value)}
              placeholder="e.g. 1  or  8" />

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
                {visibleCols.has('Name')        && <th>Name</th>}
                {visibleCols.has('IP')          && <th>IP</th>}
                {visibleCols.has('Description') && <th>Description</th>}
                {visibleCols.has('Bits')        && <th>Bits</th>}
                {visibleCols.has('Default')     && <th>Default</th>}
                {visibleCols.has('Group')       && <th>Group</th>}
              </tr>
            </thead>
            <tbody>
              {paginated.map(f => (
                <tr key={f.Name} className={selected.has(f.Name) ? 'row-selected' : ''}>
                  <td><input type="checkbox" checked={selected.has(f.Name)} onChange={() => toggle(f.Name)} /></td>
                  {visibleCols.has('Name')        && <td className="fuse-name">{f.Name}</td>}
                  {visibleCols.has('IP')          && <td className="fuse-ip">{f.IP}</td>}
                  {visibleCols.has('Description') && <td className="fuse-desc">{f.Description}</td>}
                  {visibleCols.has('Bits')        && <td className="fuse-bits">{f.Bits}</td>}
                  {visibleCols.has('Default')     && <td className="fuse-def">{f.Default}</td>}
                  {visibleCols.has('Group')       && <td className="fuse-grp">{f.Group}</td>}
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
