import React, { useState, useRef, useCallback } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function useFileList() {
  const [files, setFiles] = useState<File[]>([]);
  const add = useCallback((newFiles: File[]) => {
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name));
      return [...prev, ...newFiles.filter(f => !names.has(f.name))];
    });
  }, []);
  const remove = (name: string) => setFiles(prev => prev.filter(f => f.name !== name));
  const clear = () => setFiles([]);
  return { files, add, remove, clear };
}

function DropZone({ onFiles, multi = false, accept = '.xlsx,.xls', label }: {
  onFiles: (f: File[]) => void; multi?: boolean; accept?: string; label: string;
}) {
  const [dragging, setDragging] = useState(false);
  const ref = useRef<HTMLInputElement>(null);
  return (
    <div
      className={`drop-zone${dragging ? ' drag-over' : ''}`}
      onClick={() => ref.current?.click()}
      onDragOver={e => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={e => { e.preventDefault(); setDragging(false); onFiles(Array.from(e.dataTransfer.files)); }}
    >
      <input ref={ref} type="file" accept={accept} multiple={multi} style={{ display: 'none' }}
        onChange={e => { if (e.target.files) onFiles(Array.from(e.target.files)); e.target.value = ''; }} />
      <div className="drop-icon">📂</div>
      <div className="drop-hint">{label}</div>
    </div>
  );
}

function FileListView({ files, onRemove }: { files: File[]; onRemove: (n: string) => void }) {
  if (!files.length) return null;
  return (
    <div className="file-list">
      {files.map(f => (
        <div key={f.name} className="file-item">
          <span className="file-name">📄 {f.name}</span>
          <button className="btn" onClick={() => onRemove(f.name)}>✕</button>
        </div>
      ))}
    </div>
  );
}

function MergeTab() {
  const fl = useFileList();
  const [prefix,  setPrefix]  = useState('');
  const [outName, setOutName] = useState('merged_output');
  const [loading, setLoading] = useState(false);
  const [log,     setLog]     = useState('');
  const addLog = (m: string) => setLog(l => l + m + '\n');

  const handleMerge = async () => {
    if (!fl.files.length) { addLog('[ERROR] No files selected.'); return; }
    setLoading(true); setLog('');
    addLog(`[INFO] Merging ${fl.files.length} file(s)...`);
    const fd = new FormData();
    fl.files.forEach(f => fd.append('files', f));
    fd.append('prefix', prefix);
    fd.append('output_name', outName);
    try {
      const resp = await fetch(`${BASE}/files/merge`, { method: 'POST', body: fd });
      if (!resp.ok) { addLog(`[ERROR] ${resp.status}: ${await resp.text()}`); }
      else {
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') ?? '';
        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fname = match ? match[1].replace(/['"]/g, '') : `${outName}.xlsx`;
        downloadBlob(blob, fname);
        addLog(`[OK] Downloaded: ${fname}`);
      }
    } catch (e: unknown) {
      addLog(`[ERROR] ${(e as Error).message}`);
    } finally { setLoading(false); }
  };

  return (
    <div className="tab-content">
      <div className="fh-layout">
        <div className="panel">
          <div className="section-title">Configuration</div>
          <div className="form-grid">
            <label>Prefix Filter</label>
            <input value={prefix} onChange={e => setPrefix(e.target.value)} placeholder="Optional prefix" />
            <label>Output Name</label>
            <input value={outName} onChange={e => setOutName(e.target.value)} placeholder="merged_output" />
          </div>
        </div>
        <div className="panel">
          <div className="section-title">Excel Files</div>
          <DropZone multi onFiles={fl.add} label="Drop .xlsx / .xls files or click to browse" />
          <FileListView files={fl.files} onRemove={fl.remove} />
          <div className="action-row" style={{ marginTop: 10 }}>
            <button className="btn primary" onClick={handleMerge} disabled={loading || !fl.files.length}>
              {loading ? '⏳ Merging…' : '▶ Merge Files'}
            </button>
            {fl.files.length > 0 && <button className="btn" onClick={fl.clear}>🗑 Clear</button>}
          </div>
        </div>
      </div>
      <div className="panel" style={{ marginTop: 12 }}>
        <div className="section-title">Log</div>
        <div className="log-area" style={{ height: 110 }}>{log || 'Ready.'}</div>
      </div>
    </div>
  );
}

function AppendTab() {
  const [source,  setSource]  = useState<File | null>(null);
  const [target,  setTarget]  = useState<File | null>(null);
  const [sheets,  setSheets]  = useState('');
  const [loading, setLoading] = useState(false);
  const [log,     setLog]     = useState('');
  const addLog = (m: string) => setLog(l => l + m + '\n');

  const handleAppend = async () => {
    if (!source || !target) { addLog('[ERROR] Both source and target files required.'); return; }
    setLoading(true); setLog('');
    addLog(`[INFO] Appending ${source.name} → ${target.name}...`);
    const fd = new FormData();
    fd.append('source', source);
    fd.append('target', target);
    fd.append('sheets', sheets);
    try {
      const resp = await fetch(`${BASE}/files/append`, { method: 'POST', body: fd });
      if (!resp.ok) { addLog(`[ERROR] ${resp.status}: ${await resp.text()}`); }
      else {
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') ?? '';
        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fname = match ? match[1].replace(/['"]/g, '') : 'appended.xlsx';
        downloadBlob(blob, fname);
        addLog(`[OK] Downloaded: ${fname}`);
      }
    } catch (e: unknown) {
      addLog(`[ERROR] ${(e as Error).message}`);
    } finally { setLoading(false); }
  };

  return (
    <div className="tab-content">
      <div className="fh-layout">
        <div className="panel">
          <div className="section-title">Source File (data to append)</div>
          <DropZone onFiles={f => setSource(f[0])} label="Drop source .xlsx / .xls or click" />
          {source && <div className="selected-file">📄 {source.name} <button className="btn" onClick={() => setSource(null)}>✕</button></div>}
        </div>
        <div className="panel">
          <div className="section-title">Target File (file to append into)</div>
          <DropZone onFiles={f => setTarget(f[0])} label="Drop target .xlsx / .xls or click" />
          {target && <div className="selected-file">📄 {target.name} <button className="btn" onClick={() => setTarget(null)}>✕</button></div>}
        </div>
      </div>
      <div className="panel" style={{ marginTop: 12 }}>
        <div className="section-title">Sheet Names (comma-separated)</div>
        <input
          style={{ width: '100%' }}
          value={sheets}
          onChange={e => setSheets(e.target.value)}
          placeholder="Sheet1, Sheet2 (leave blank for all)"
        />
        <div className="action-row" style={{ marginTop: 10 }}>
          <button className="btn primary" onClick={handleAppend} disabled={loading || !source || !target}>
            {loading ? '⏳ Appending…' : '▶ Append Sheets'}
          </button>
        </div>
      </div>
      <div className="panel" style={{ marginTop: 12 }}>
        <div className="section-title">Log</div>
        <div className="log-area" style={{ height: 110 }}>{log || 'Ready.'}</div>
      </div>
    </div>
  );
}

export default function FileHandler() {
  const [tab, setTab] = useState<'merge' | 'append'>('merge');
  return (
    <div className="tool-page">
      <h2 className="page-title">📁 File Handler</h2>
      <div className="tab-bar">
        <button className={`tab-btn${tab === 'merge' ? ' active' : ''}`} onClick={() => setTab('merge')}>Merge</button>
        <button className={`tab-btn${tab === 'append' ? ' active' : ''}`} onClick={() => setTab('append')}>Append</button>
      </div>
      {tab === 'merge' ? <MergeTab /> : <AppendTab />}
    </div>
  );
}
