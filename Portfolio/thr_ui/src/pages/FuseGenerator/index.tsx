import React, { useState, useEffect, useMemo } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';
const PAGE_SIZE = 200;

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

interface Fuse {
  Name: string;
  IP: string;
  Description: string;
  Bits: string;
  Default: string;
  Group: string;
}

export default function FuseGenerator() {
  const [product,   setProduct]   = useState('GNR');
  const [fuses,     setFuses]     = useState<Fuse[]>([]);
  const [ips,       setIps]       = useState<string[]>([]);
  const [groups,    setGroups]    = useState<string[]>([]);
  const [search,    setSearch]    = useState('');
  const [filterIp,  setFilterIp]  = useState('');
  const [filterGrp, setFilterGrp] = useState('');
  const [selected,  setSelected]  = useState<Set<string>>(new Set());
  const [filename,  setFilename]  = useState('fuses_output');
  const [loading,   setLoading]   = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error,     setError]     = useState('');
  const [page,      setPage]      = useState(1);

  useEffect(() => {
    setLoading(true); setError(''); setFuses([]); setSelected(new Set());
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

  // Reset to page 1 whenever filters change
  useEffect(() => { setPage(1); }, [search, filterIp, filterGrp, fuses]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return fuses.filter(f =>
      (!q || f.Name.toLowerCase().includes(q) || f.Description.toLowerCase().includes(q)) &&
      (!filterIp  || f.IP === filterIp) &&
      (!filterGrp || f.Group === filterGrp)
    );
  }, [fuses, search, filterIp, filterGrp]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paginated  = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const toggle = (name: string) =>
    setSelected(s => { const n = new Set(s); n.has(name) ? n.delete(name) : n.add(name); return n; });

  const selectAll    = () => setSelected(new Set(fuses.map(f => f.Name)));
  const clearAll     = () => setSelected(new Set());
  const selectFiltered = () => setSelected(s => { const n = new Set(s); filtered.forEach(f => n.add(f.Name)); return n; });
  const clearFiltered  = () => setSelected(s => { const n = new Set(s); filtered.forEach(f => n.delete(f.Name)); return n; });

  const handleGenerate = async () => {
    if (!selected.size) { setError('No fuses selected.'); return; }
    setGenerating(true); setError('');
    try {
      const resp = await fetch(`${BASE}/fuses/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product, selected_names: [...selected], filename }),
      });
      if (!resp.ok) { setError(`${resp.status}: ${await resp.text()}`); }
      else {
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') ?? '';
        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fname = match ? match[1].replace(/['"]/g, '') : `${filename}.fuse`;
        downloadBlob(blob, fname);
      }
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally { setGenerating(false); }
  };

  return (
    <div className="tool-page">
      <h2 className="page-title">🔌 Fuse Generator</h2>

      <div className="fg-top-row">
        <div className="panel fg-controls">
          <div className="section-title">Filters</div>
          <div className="form-grid">
            <label>Product</label>
            <select value={product} onChange={e => setProduct(e.target.value)}>
              {['GNR','CWF','DMR'].map(p => <option key={p}>{p}</option>)}
            </select>

            <label>Search</label>
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Name or description…" />

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

            <label>Output File</label>
            <input value={filename} onChange={e => setFilename(e.target.value)} placeholder="fuses_output" />
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
            <span className="badge">{selected.size}</span> selected of{' '}
            <span className="badge-dim">{fuses.length}</span> total
            {' '}(<span className="badge-dim">{filtered.length}</span> matching filter)
          </div>
          {error && <div className="error-msg" style={{ marginTop: 8 }}>{error}</div>}
          <div style={{ marginTop: 12 }}>
            <button
              className="btn primary"
              onClick={handleGenerate}
              disabled={generating || !selected.size}
              style={{ width: '100%' }}
            >
              {generating ? '⏳ Generating…' : '▶ Generate Fuse File'}
            </button>
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 12 }}>
        <div className="section-title">
          Fuses {loading && <span className="loading-badge">Loading…</span>}
        </div>
        <div className="fuse-table-wrap">
          <table className="fuse-table">
            <thead>
              <tr>
                <th><input type="checkbox"
                  checked={paginated.length > 0 && paginated.every(f => selected.has(f.Name))}
                  onChange={e => {
                    const n = new Set(selected);
                    paginated.forEach(f => e.target.checked ? n.add(f.Name) : n.delete(f.Name));
                    setSelected(n);
                  }} /></th>
                <th>Name</th>
                <th>IP</th>
                <th>Description</th>
                <th>Bits</th>
                <th>Default</th>
                <th>Group</th>
              </tr>
            </thead>
            <tbody>
              {paginated.map(f => (
                <tr key={f.Name} className={selected.has(f.Name) ? 'row-selected' : ''}>
                  <td><input type="checkbox" checked={selected.has(f.Name)} onChange={() => toggle(f.Name)} /></td>
                  <td className="fuse-name">{f.Name}</td>
                  <td className="fuse-ip">{f.IP}</td>
                  <td className="fuse-desc">{f.Description}</td>
                  <td className="fuse-bits">{f.Bits}</td>
                  <td className="fuse-def">{f.Default}</td>
                  <td className="fuse-grp">{f.Group}</td>
                </tr>
              ))}
              {!loading && filtered.length === 0 && (
                <tr><td colSpan={7} style={{ textAlign: 'center', color: '#858585', padding: 16 }}>
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
            <span className="pg-info">Page {page} / {totalPages} &nbsp;·&nbsp; {filtered.length.toLocaleString()} rows</span>
            <button className="btn" onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>›</button>
            <button className="btn" onClick={() => setPage(totalPages)} disabled={page === totalPages}>»</button>
          </div>
        )}
      </div>
    </div>
  );
}
