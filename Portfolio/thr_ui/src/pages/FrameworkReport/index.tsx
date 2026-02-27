import React, { useState, useRef, useCallback, useEffect } from 'react';

import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';
const DATA_SERVER = '\\\\crcv03a-cifs.cr.intel.com\\mfg_tlo_001\\DebugFramework';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

const CONTENT_OPTIONS = ['Dragon', 'Linux', 'TSL', 'Python', 'Sandstone', 'EFI', 'Pseudo Slice', 'Pseudo Mesh', 'Imunch', 'Other'];
const TYPE_OPTIONS    = ['Baseline', 'Loops', 'Voltage', 'Frequency', 'Shmoo', 'Others', 'Invalid'];
const PRODUCTS        = ['GNR', 'CWF', 'DMR'];

interface Experiment {
  name: string;
  include: boolean;
  content: string;
  type: string;
  otherType: string;
  comments: string;
}

interface ReportOptions {
  merge:        boolean;
  mergeTag:     string;
  generate:     boolean;
  reportTag:    string;
  checkLogging: boolean;
  skipStrings:  string;
  dragonData:   boolean;
  coreData:     boolean;
  summaryTab:   boolean;
  overview:     boolean;
  outputName:   string;
}

type InputMode = 'path' | 'zip';

export default function FrameworkReport() {
  const [inputMode,  setInputMode]  = useState<InputMode>('path');
  const [product,    setProduct]    = useState('GNR');
  const [vids,       setVids]       = useState<string[]>([]);
  const [vid,        setVid]        = useState('');
  const [folderPath, setFolderPath] = useState('');
  const [zipFile,    setZipFile]    = useState<File | null>(null);
  const [dragging,   setDragging]   = useState(false);
  const [exps,       setExps]       = useState<Experiment[]>([]);
  const [parsed,     setParsed]     = useState(false);
  const [loading,    setLoading]    = useState(false);
  const [generating, setGenerating] = useState(false);
  const [log,        setLog]        = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const [opts, setOpts] = useState<ReportOptions>({
    merge: false, mergeTag: '', generate: true, reportTag: '',
    checkLogging: false, skipStrings: '', dragonData: true,
    coreData: true, summaryTab: false, overview: true, outputName: 'framework_report',
  });

  const addLog = (m: string) => setLog(l => l + m + '\n');
  const setOpt = <K extends keyof ReportOptions>(k: K, v: ReportOptions[K]) =>
    setOpts(o => ({ ...o, [k]: v }));

  // Load VIDs when product changes
  useEffect(() => {
    setVids([]); setVid('');
    fetch(`${BASE}/framework/vids?product=${product}`)
      .then(r => r.json())
      .then(d => { setVids(d.vids ?? []); })
      .catch(() => {});
  }, [product]);

  // Auto-set folder path when VID is selected
  useEffect(() => {
    if (vid) {
      setFolderPath(`${DATA_SERVER}\\${product}\\${vid}`);
    }
  }, [vid, product]);

  const handleZipDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) { setZipFile(f); setParsed(false); setExps([]); }
  }, []);

  const handleScan = async () => {
    const path = folderPath.trim();
    if (!path) { addLog('[ERROR] No folder path set.'); return; }
    setLoading(true); setLog(''); setParsed(false);
    addLog(`[INFO] Scanning ${path}...`);
    const fd = new FormData();
    fd.append('folder_path', path);
    try {
      const resp = await fetch(`${BASE}/framework/scan`, { method: 'POST', body: fd });
      if (!resp.ok) { addLog(`[ERROR] ${resp.status}: ${await resp.text()}`); }
      else {
        const data = await resp.json();
        const names: string[] = data.experiments ?? [];
        setExps(names.map(name => ({
          name, include: true,
          content: 'Dragon', type: 'Baseline', otherType: '', comments: '',
        })));
        setParsed(true);
        addLog(`[OK] Found ${names.length} experiment(s).`);
      }
    } catch (e: unknown) {
      addLog(`[ERROR] ${(e as Error).message}`);
    } finally { setLoading(false); }
  };

  const handleParse = async () => {
    if (!zipFile) { addLog('[ERROR] No ZIP file selected.'); return; }
    setLoading(true); setLog(''); setParsed(false);
    addLog(`[INFO] Parsing ${zipFile.name}...`);
    const fd = new FormData();
    fd.append('zip_file', zipFile);
    try {
      const resp = await fetch(`${BASE}/framework/parse`, { method: 'POST', body: fd });
      if (!resp.ok) { addLog(`[ERROR] ${resp.status}: ${await resp.text()}`); }
      else {
        const data = await resp.json();
        const names: string[] = data.experiments ?? Object.keys(data);
        setExps(names.map(name => ({
          name, include: true,
          content: 'Dragon', type: 'Baseline', otherType: '', comments: '',
        })));
        setParsed(true);
        addLog(`[OK] Found ${names.length} experiment(s).`);
      }
    } catch (e: unknown) {
      addLog(`[ERROR] ${(e as Error).message}`);
    } finally { setLoading(false); }
  };

  const updateExp = <K extends keyof Experiment>(idx: number, key: K, val: Experiment[K]) =>
    setExps(prev => prev.map((e, i) => i === idx ? { ...e, [key]: val } : e));

  const selectAll   = () => setExps(prev => prev.map(e => ({ ...e, include: true })));
  const deselectAll = () => setExps(prev => prev.map(e => ({ ...e, include: false })));

  const handleGenerate = async () => {
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setGenerating(true);
    addLog('[INFO] Generating report...');

    try {
      let resp: Response;
      if (inputMode === 'path') {
        const fd = new FormData();
        fd.append('folder_path',      folderPath);
        fd.append('experiments_json', JSON.stringify(exps));
        fd.append('merge',            String(opts.merge));
        fd.append('merge_tag',        opts.mergeTag);
        fd.append('generate',         String(opts.generate));
        fd.append('report_tag',       opts.reportTag);
        fd.append('check_logging',    String(opts.checkLogging));
        fd.append('skip_strings',     opts.skipStrings);
        fd.append('dragon_data',      String(opts.dragonData));
        fd.append('core_data',        String(opts.coreData));
        fd.append('summary_tab',      String(opts.summaryTab));
        fd.append('overview',         String(opts.overview));
        fd.append('output_name',      opts.outputName);
        resp = await fetch(`${BASE}/framework/generate_from_path`, {
          method: 'POST', body: fd, signal: ctrl.signal,
        });
      } else {
        if (!zipFile) { addLog('[ERROR] ZIP file missing.'); setGenerating(false); return; }
        const fd = new FormData();
        fd.append('zip_file',         zipFile);
        fd.append('experiments_json', JSON.stringify(exps));
        fd.append('merge',            String(opts.merge));
        fd.append('merge_tag',        opts.mergeTag);
        fd.append('generate',         String(opts.generate));
        fd.append('report_tag',       opts.reportTag);
        fd.append('check_logging',    String(opts.checkLogging));
        fd.append('skip_strings',     opts.skipStrings);
        fd.append('dragon_data',      String(opts.dragonData));
        fd.append('core_data',        String(opts.coreData));
        fd.append('summary_tab',      String(opts.summaryTab));
        fd.append('overview',         String(opts.overview));
        fd.append('output_name',      opts.outputName);
        resp = await fetch(`${BASE}/framework/generate`, {
          method: 'POST', body: fd, signal: ctrl.signal,
        });
      }
      if (!resp.ok) { addLog(`[ERROR] ${resp.status}: ${await resp.text()}`); }
      else {
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') ?? '';
        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fname = match ? match[1].replace(/['"]/g, '') : `${opts.outputName}.xlsx`;
        downloadBlob(blob, fname);
        addLog(`[OK] Downloaded: ${fname}`);
      }
    } catch (e: unknown) {
      if ((e as Error).name !== 'AbortError') addLog(`[ERROR] ${(e as Error).message}`);
      else addLog('[INFO] Cancelled.');
    } finally { setGenerating(false); abortRef.current = null; }
  };

  return (
    <div className="tool-page">
      <h2 className="page-title">📊 Framework Report</h2>

      {/* Input mode toggle */}
      <div className="panel" style={{ marginBottom: 12 }}>
        <div className="section-title">Input Mode</div>
        <div className="action-row">
          <button
            className={`btn ${inputMode === 'path' ? 'primary' : ''}`}
            onClick={() => { setInputMode('path'); setParsed(false); setExps([]); }}
          >🗂 Server / Network Path</button>
          <button
            className={`btn ${inputMode === 'zip' ? 'primary' : ''}`}
            onClick={() => { setInputMode('zip'); setParsed(false); setExps([]); }}
          >📦 Upload ZIP</button>
        </div>
      </div>

      {/* Step 1: Data Source */}
      <div className="panel" style={{ marginBottom: 12 }}>
        <div className="section-title">Step 1 — Data Source</div>

        {inputMode === 'path' ? (
          <div>
            <div className="form-grid">
              <label>Product</label>
              <select value={product} onChange={e => setProduct(e.target.value)}>
                {PRODUCTS.map(p => <option key={p}>{p}</option>)}
              </select>

              <label>Visual ID (VID)</label>
              <select value={vid} onChange={e => setVid(e.target.value)}>
                <option value="">— select VID —</option>
                {vids.map(v => <option key={v}>{v}</option>)}
              </select>

              <label>Folder Path</label>
              <input
                value={folderPath}
                onChange={e => setFolderPath(e.target.value)}
                placeholder={`${DATA_SERVER}\\${product}\\<VID>`}
                style={{ fontFamily: 'monospace', fontSize: 12 }}
              />
            </div>
            <div style={{ marginTop: 8 }}>
              <button className="btn primary" onClick={handleScan} disabled={loading || !folderPath}>
                {loading ? '⏳ Scanning…' : '🔍 Scan Folder'}
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="fr-upload-row">
              <div
                className={`drop-zone drop-zone-inline${dragging ? ' drag-over' : ''}${zipFile ? ' has-file' : ''}`}
                onClick={() => inputRef.current?.click()}
                onDragOver={e => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleZipDrop}
              >
                <input ref={inputRef} type="file" accept=".zip" style={{ display: 'none' }}
                  onChange={e => { const f = e.target.files?.[0]; if (f) { setZipFile(f); setParsed(false); setExps([]); } }} />
                {zipFile ? <span>📦 {zipFile.name}</span> : <span>📂 Drop .zip here or click to browse</span>}
              </div>
              <button className="btn primary" onClick={handleParse} disabled={loading || !zipFile} style={{ flexShrink: 0 }}>
                {loading ? '⏳ Parsing…' : '▶ Parse ZIP'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Step 2: Experiment Table */}
      {parsed && exps.length > 0 && (
        <div className="panel" style={{ marginBottom: 12 }}>
          <div className="section-title-row">
            <span className="section-title" style={{ margin: 0, border: 0 }}>
              Step 2 — Experiments ({exps.length})
            </span>
            <div className="action-row">
              <button className="btn" onClick={selectAll}>☑ Select All</button>
              <button className="btn" onClick={deselectAll}>☐ Deselect All</button>
            </div>
          </div>
          <div className="exp-table-wrap">
            <table className="exp-table">
              <thead>
                <tr>
                  <th>✓</th>
                  <th>Experiment</th>
                  <th>Content</th>
                  <th>Type</th>
                  <th>Other Type</th>
                  <th>Comments</th>
                </tr>
              </thead>
              <tbody>
                {exps.map((exp, i) => (
                  <tr key={exp.name} className={exp.include ? '' : 'exp-row-off'}>
                    <td>
                      <input type="checkbox" checked={exp.include}
                        onChange={e => updateExp(i, 'include', e.target.checked)} />
                    </td>
                    <td className="exp-name">{exp.name}</td>
                    <td>
                      <select value={exp.content} onChange={e => updateExp(i, 'content', e.target.value)}>
                        {CONTENT_OPTIONS.map(c => <option key={c}>{c}</option>)}
                      </select>
                    </td>
                    <td>
                      <select value={exp.type} onChange={e => updateExp(i, 'type', e.target.value)}>
                        {TYPE_OPTIONS.map(t => <option key={t}>{t}</option>)}
                      </select>
                    </td>
                    <td>
                      <input value={exp.otherType} onChange={e => updateExp(i, 'otherType', e.target.value)}
                        placeholder="—" style={{ width: 90 }} />
                    </td>
                    <td>
                      <input value={exp.comments} onChange={e => updateExp(i, 'comments', e.target.value)}
                        placeholder="—" style={{ width: 140 }} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Report Options */}
      {parsed && (
        <div className="panel" style={{ marginBottom: 12 }}>
          <div className="section-title">Step 3 — Report Options</div>
          <div className="opts-grid">
            <label className="check-label">
              <input type="checkbox" checked={opts.merge} onChange={e => setOpt('merge', e.target.checked)} />
              Merge Summary Files
            </label>
            <input value={opts.mergeTag} onChange={e => setOpt('mergeTag', e.target.value)}
              placeholder="Merge tag" disabled={!opts.merge} />

            <label className="check-label">
              <input type="checkbox" checked={opts.generate} onChange={e => setOpt('generate', e.target.checked)} />
              Generate Report
            </label>
            <input value={opts.reportTag} onChange={e => setOpt('reportTag', e.target.value)}
              placeholder="Report tag" disabled={!opts.generate} />

            <label className="check-label">
              <input type="checkbox" checked={opts.checkLogging} onChange={e => setOpt('checkLogging', e.target.checked)} />
              Check Logging Data
            </label>
            <input value={opts.skipStrings} onChange={e => setOpt('skipStrings', e.target.value)}
              placeholder="Skip strings (comma-sep)" disabled={!opts.checkLogging} />

            <label className="check-label">
              <input type="checkbox" checked={opts.dragonData} onChange={e => setOpt('dragonData', e.target.checked)} />
              Generate DragonData Sheet
            </label>
            <span />

            <label className="check-label">
              <input type="checkbox" checked={opts.coreData} onChange={e => setOpt('coreData', e.target.checked)} />
              CoreData Sheet
            </label>
            <span />

            <label className="check-label">
              <input type="checkbox" checked={opts.summaryTab} onChange={e => setOpt('summaryTab', e.target.checked)} />
              Summary Tab
            </label>
            <span />

            <label className="check-label">
              <input type="checkbox" checked={opts.overview} onChange={e => setOpt('overview', e.target.checked)} />
              Unit Overview
            </label>
            <span />

            <label>Output Name</label>
            <input value={opts.outputName} onChange={e => setOpt('outputName', e.target.value)} placeholder="framework_report" />
          </div>

          <div className="action-row" style={{ marginTop: 14 }}>
            <button
              className="btn primary"
              onClick={handleGenerate}
              disabled={generating || (inputMode === 'zip' && !zipFile) || (inputMode === 'path' && !folderPath)}
            >
              {generating ? '⏳ Generating…' : '▶ Generate Report'}
            </button>
            {generating && (
              <button className="btn danger" onClick={() => abortRef.current?.abort()}>✕ Cancel</button>
            )}
          </div>
        </div>
      )}

      <div className="panel">
        <div className="section-title">Log</div>
        <div className="log-area" style={{ height: 130 }}>{log || 'Ready.'}</div>
      </div>
    </div>
  );
}

