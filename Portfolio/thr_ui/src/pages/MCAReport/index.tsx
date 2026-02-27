import React, { useState, useRef, useCallback } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

type CheckboxOption = { key: string; label: string };
const OPTIONS: CheckboxOption[] = [
  { key: 'reduced',   label: 'Reduced Report' },
  { key: 'decode',    label: 'MCA Decode' },
  { key: 'overview',  label: 'Overview Sheet' },
  // MC Checker option has been removed (deprecated)
];

export default function MCAReport() {
  const [mode,      setMode]      = useState('Bucketer');   // default: Bucketer
  const [product,   setProduct]   = useState('GNR');
  const [workWeek,  setWorkWeek]  = useState('WW9');
  const [label,     setLabel]     = useState('');
  // default: all three options enabled
  const [opts,      setOpts]      = useState<Record<string,boolean>>({
    reduced: true, decode: true, overview: true,
  });
  const [file,      setFile]      = useState<File | null>(null);
  const [dragging,  setDragging]  = useState(false);
  const [loading,   setLoading]   = useState(false);
  const [log,       setLog]       = useState('');
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const addLog = (msg: string) => setLog(l => l + msg + '\n');

  const toggleOpt = (k: string) =>
    setOpts(o => ({ ...o, [k]: !o[k] }));

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
    addLog(`[INFO] Sending request...`);
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
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') ?? '';
        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fname = match ? match[1].replace(/['"]/g, '') : 'mca_report.xlsx';
        downloadBlob(blob, fname);
        addLog(`[OK] Downloaded: ${fname}`);
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

      <div className="panel" style={{ marginTop: 12 }}>
        <div className="section-title">Log</div>
        <div className="log-area" style={{ height: 140 }}>
          {log || 'Ready.'}
        </div>
      </div>
    </div>
  );
}
