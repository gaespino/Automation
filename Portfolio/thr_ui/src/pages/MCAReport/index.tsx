import React, { useState, useRef, useCallback } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

type CheckboxOption = { key: string; label: string };
const OPTIONS: CheckboxOption[] = [
  { key: 'reduced',   label: 'Reduced Report' },
  { key: 'decode',    label: 'MCA Decode' },
  { key: 'overview',  label: 'Overview Sheet' },
  // MC Checker option has been removed (deprecated)
];

interface OutputFile { name: string; size: number; }
interface ReportResult { token: string; files: OutputFile[]; }

export default function MCAReport() {
  const [mode,      setMode]      = useState('Bucketer');
  const [product,   setProduct]   = useState('GNR');
  const [workWeek,  setWorkWeek]  = useState('WW9');
  const [label,     setLabel]     = useState('');
  const [opts,      setOpts]      = useState<Record<string,boolean>>({
    reduced: true, decode: true, overview: true,
  });
  const [file,      setFile]      = useState<File | null>(null);
  const [dragging,  setDragging]  = useState(false);
  const [loading,   setLoading]   = useState(false);
  const [log,       setLog]       = useState('');

  // Post-generation state
  const [result,    setResult]    = useState<ReportResult | null>(null);
  const [selected,  setSelected]  = useState<Set<string>>(new Set());
  const [savePath,  setSavePath]  = useState('');
  const [actioning, setActioning] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const addLog = (msg: string) => setLog(l => l + msg + '\n');

  const toggleOpt = (k: string) =>
    setOpts(o => ({ ...o, [k]: !o[k] }));

  const toggleFile = (name: string) =>
    setSelected(s => {
      const n = new Set(s);
      if (n.has(name)) n.delete(name); else n.add(name);
      return n;
    });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  const handleGenerate = async () => {
    if (!file) { addLog('[ERROR] No file selected.'); return; }
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setLoading(true);
    setLog('');
    setResult(null);
    addLog(`[INFO] Sending request…`);
    addLog(`[INFO] File: ${file.name}`);

    const selectedOpts = OPTIONS.filter(o => opts[o.key]).map(o => o.key).join(',');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('mode', mode);
    fd.append('product', product);
    fd.append('work_week', workWeek);
    fd.append('label', label);
    fd.append('options', selectedOpts);

    try {
      const resp = await fetch(`${BASE}/mca/report`, {
        method: 'POST', body: fd, signal: ctrl.signal,
      });
      if (!resp.ok) {
        const text = await resp.text();
        addLog(`[ERROR] ${resp.status}: ${text}`);
      } else {
        const data: ReportResult = await resp.json();
        setResult(data);
        setSelected(new Set(data.files.map(f => f.name)));
        addLog(`[OK] Report ready — ${data.files.length} file(s) generated.`);
        data.files.forEach(f => addLog(`       📄 ${f.name}  (${formatBytes(f.size)})`));
      }
    } catch (err: unknown) {
      if ((err as Error).name !== 'AbortError') addLog(`[ERROR] ${(err as Error).message}`);
      else addLog('[INFO] Cancelled.');
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  };

  const handleCancel = () => {
    abortRef.current?.abort();
    setLoading(false);
    addLog('[INFO] Cancelled by user.');
  };

  const handleDownload = async () => {
    if (!result || selected.size === 0) return;
    setActioning(true);
    addLog(`[INFO] Downloading ${selected.size} file(s)…`);
    try {
      const fd = new FormData();
      fd.append('token', result.token);
      fd.append('filenames', Array.from(selected).join(','));
      const resp = await fetch(`${BASE}/mca/download`, { method: 'POST', body: fd });
      if (!resp.ok) {
        const text = await resp.text();
        addLog(`[ERROR] Download failed: ${text}`);
      } else {
        const blob = await resp.blob();
        downloadBlob(blob, 'MCAReport.zip');
        addLog(`[OK] Downloaded MCAReport.zip`);
      }
    } catch (err: unknown) {
      addLog(`[ERROR] ${(err as Error).message}`);
    } finally {
      setActioning(false);
    }
  };

  const handleSave = async () => {
    if (!result || selected.size === 0 || !savePath.trim()) return;
    setActioning(true);
    addLog(`[INFO] Saving ${selected.size} file(s) to: ${savePath}…`);
    try {
      const fd = new FormData();
      fd.append('token', result.token);
      fd.append('filenames', Array.from(selected).join(','));
      fd.append('dest_path', savePath.trim());
      const resp = await fetch(`${BASE}/mca/save`, { method: 'POST', body: fd });
      const data = await resp.json();
      if (!resp.ok) {
        addLog(`[ERROR] Save failed: ${data.detail ?? JSON.stringify(data)}`);
      } else {
        addLog(`[OK] Saved ${data.saved.length} file(s) to: ${data.dest_path}`);
        data.saved.forEach((f: string) => addLog(`       💾 ${f}`));
      }
    } catch (err: unknown) {
      addLog(`[ERROR] ${(err as Error).message}`);
    } finally {
      setActioning(false);
    }
  };

  return (
    <div className="tool-page">
      <h2 className="page-title">📋 MCA Report</h2>

      <div className="mca-layout">
        <div className="panel">
          <div className="section-title">Configuration</div>
          <div className="form-grid">
            <label>Mode</label>
            <select value={mode} onChange={e => setMode(e.target.value)}>
              {['Bucketer','Framework','Data'].map(m => <option key={m}>{m}</option>)}
            </select>

            <label>Product</label>
            <select value={product} onChange={e => setProduct(e.target.value)}>
              {['GNR','CWF','DMR'].map(p => <option key={p}>{p}</option>)}
            </select>

            <label>Work Week</label>
            <input value={workWeek} onChange={e => setWorkWeek(e.target.value)} placeholder="WW9" />

            <label>Label</label>
            <input value={label} onChange={e => setLabel(e.target.value)} placeholder="Optional label" />
          </div>

          <div className="section-title" style={{ marginTop: 12 }}>Options</div>
          <div className="checkbox-group">
            {OPTIONS.map(o => (
              <label key={o.key} className="check-label">
                <input type="checkbox" checked={!!opts[o.key]} onChange={() => toggleOpt(o.key)} />
                {o.label}
              </label>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="section-title">Input File</div>
          <div
            className={`drop-zone${dragging ? ' drag-over' : ''}${file ? ' has-file' : ''}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xls"
              style={{ display: 'none' }}
              onChange={e => { if (e.target.files?.[0]) setFile(e.target.files[0]); }}
            />
            {file
              ? <><div className="drop-filename">📄 {file.name}</div><div className="drop-hint">Click or drag to replace</div></>
              : <><div className="drop-icon">📂</div><div className="drop-hint">Drop .xlsx / .xls here or click to browse</div></>
            }
          </div>
          {file && (
            <button className="btn" style={{ marginTop: 6 }} onClick={() => setFile(null)}>✕ Remove file</button>
          )}

          <div className="action-row" style={{ marginTop: 14 }}>
            <button
              className="btn primary"
              onClick={handleGenerate}
              disabled={loading || !file}
            >
              {loading ? '⏳ Generating…' : '▶ Generate Report'}
            </button>
            {loading && (
              <button className="btn danger" onClick={handleCancel}>✕ Cancel</button>
            )}
          </div>
        </div>
      </div>

      {/* Output file list — shown after a successful report generation */}
      {result && (
        <div className="panel" style={{ marginTop: 12 }}>
          <div className="section-title">Output Files</div>
          <div className="file-list">
            {result.files.map(f => (
              <label key={f.name} className="check-label file-list-row">
                <input
                  type="checkbox"
                  checked={selected.has(f.name)}
                  onChange={() => toggleFile(f.name)}
                />
                <span className="file-entry-name">📄 {f.name}</span>
                <span className="dim">{formatBytes(f.size)}</span>
              </label>
            ))}
          </div>

          <div className="files-actions">
            <div className="files-action-block">
              <div className="files-action-title">⬇ Download as ZIP</div>
              <div className="files-action-desc dim">Download selected files to your computer as a ZIP archive.</div>
              <button
                className="btn primary"
                onClick={handleDownload}
                disabled={actioning || selected.size === 0}
              >
                ⬇ Download selected ({selected.size})
              </button>
            </div>

            <div className="files-action-divider" />

            <div className="files-action-block">
              <div className="files-action-title">💾 Save to path</div>
              <div className="files-action-desc dim">Save selected files directly to a folder on the server.</div>
              <div className="save-row">
                <input
                  type="text"
                  className="save-path-input"
                  placeholder="e.g. C:\output\MCA or /home/user/output"
                  value={savePath}
                  onChange={e => setSavePath(e.target.value)}
                />
                <button
                  className="btn success"
                  onClick={handleSave}
                  disabled={actioning || selected.size === 0 || !savePath.trim()}
                >
                  💾 Save selected ({selected.size})
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="panel" style={{ marginTop: 12 }}>
        <div className="section-title">Log</div>
        <div className="log-area" style={{ height: 140 }}>
          {log || 'Ready.'}
        </div>
      </div>
    </div>
  );
}
