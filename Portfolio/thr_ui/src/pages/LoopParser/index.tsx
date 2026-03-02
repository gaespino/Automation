import React, { useState, useRef, useCallback } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

export default function LoopParser() {
  const [files,       setFiles]       = useState<File[]>([]);
  const [dragging,    setDragging]    = useState(false);
  const [startWW,     setStartWW]     = useState('WW1');
  const [bucket,      setBucket]      = useState('PPV');
  const [seqKey,      setSeqKey]      = useState('100');
  const [pysvFmt,     setPysvFmt]     = useState(false);
  const [zipMode,     setZipMode]     = useState(false);
  const [outputName,  setOutputName]  = useState('loop_output');
  const [loading,     setLoading]     = useState(false);
  const [log,         setLog]         = useState('');
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const addLog = (msg: string) => setLog(l => l + msg + '\n');

  const addFiles = useCallback((newFiles: File[]) => {
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name));
      return [...prev, ...newFiles.filter(f => !names.has(f.name))];
    });
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    addFiles(Array.from(e.dataTransfer.files));
  }, [addFiles]);

  const removeFile = (name: string) =>
    setFiles(prev => prev.filter(f => f.name !== name));

  const handleParse = async () => {
    if (files.length === 0) { addLog('[ERROR] No files selected.'); return; }
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setLoading(true); setLog('');
    addLog(`[INFO] Parsing ${files.length} file(s)...`);

    const fd = new FormData();
    files.forEach(f => fd.append('files', f));
    fd.append('start_ww',     startWW);
    fd.append('bucket',       bucket);
    fd.append('seq_key',      seqKey);
    fd.append('pysv_format',  String(pysvFmt));
    fd.append('zipfile_mode', String(zipMode));
    fd.append('output_name',  outputName);

    try {
      const resp = await fetch(`${BASE}/loops/parse`, {
        method: 'POST', body: fd, signal: ctrl.signal,
      });
      if (!resp.ok) {
        const t = await resp.text();
        addLog(`[ERROR] ${resp.status}: ${t}`);
      } else {
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') ?? '';
        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fname = match ? match[1].replace(/['"]/g, '') : `${outputName}.xlsx`;
        downloadBlob(blob, fname);
        addLog(`[OK] Downloaded: ${fname}`);
      }
    } catch (e: unknown) {
      if ((e as Error).name !== 'AbortError') addLog(`[ERROR] ${(e as Error).message}`);
      else addLog('[INFO] Cancelled.');
    } finally {
      setLoading(false); abortRef.current = null;
    }
  };

  return (
    <div className="tool-page">
      <h2 className="page-title">🔄 Loop Parser</h2>

      <div className="lp-layout">
        <div className="panel">
          <div className="section-title">Configuration</div>
          <div className="form-grid">
            <label>Work Week</label>
            <input value={startWW} onChange={e => setStartWW(e.target.value)} placeholder="WW1" />

            <label>Bucket</label>
            <input value={bucket} onChange={e => setBucket(e.target.value)} placeholder="PPV" />

            <label>Sequence Key</label>
            <input type="number" value={seqKey} onChange={e => setSeqKey(e.target.value)} min="0" />

            <label>Output Name</label>
            <input value={outputName} onChange={e => setOutputName(e.target.value)} placeholder="loop_output" />

            <label>PySV Format</label>
            <label className="check-label">
              <input type="checkbox" checked={pysvFmt} onChange={e => setPysvFmt(e.target.checked)} />
              Enable PySV format
            </label>

            <label>ZIP Mode</label>
            <label className="check-label">
              <input type="checkbox" checked={zipMode} onChange={e => setZipMode(e.target.checked)} />
              Process ZIP files inside folder
            </label>
          </div>
        </div>

        <div className="panel">
          <div className="section-title">Input Files (.txt, .log, .zip)</div>
          <div
            className={`drop-zone${dragging ? ' drag-over' : ''}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".txt,.log,.zip"
              multiple
              style={{ display: 'none' }}
              onChange={e => { if (e.target.files) addFiles(Array.from(e.target.files)); e.target.value = ''; }}
            />
            <div className="drop-icon">📂</div>
            <div className="drop-hint">Drop .txt / .log / .zip files here or click to browse</div>
          </div>

          {files.length > 0 && (
            <div className="file-list">
              {files.map(f => (
                <div key={f.name} className="file-item">
                  <span className="file-name">📄 {f.name}</span>
                  <button className="btn" onClick={() => removeFile(f.name)}>✕</button>
                </div>
              ))}
            </div>
          )}

          <div className="action-row" style={{ marginTop: 10 }}>
            <button
              className="btn primary"
              onClick={handleParse}
              disabled={loading || files.length === 0}
            >
              {loading ? '⏳ Parsing…' : '▶ Parse'}
            </button>
            {loading && (
              <button className="btn danger" onClick={() => { abortRef.current?.abort(); }}>✕ Cancel</button>
            )}
            {files.length > 0 && (
              <button className="btn" onClick={() => setFiles([])}>🗑 Clear All</button>
            )}
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 12 }}>
        <div className="section-title">Log</div>
        <div className="log-area" style={{ height: 130 }}>
          {log || 'Ready.'}
        </div>
      </div>
    </div>
  );
}
