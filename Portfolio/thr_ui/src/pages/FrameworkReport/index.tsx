import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import ExcelViewer from '../../components/ExcelViewer';
import SimpleBarChart from '../../components/SimpleBarChart';
import type { BarEntry } from '../../components/SimpleBarChart';
import SweepChart from '../../components/SweepChart';
import type { SweepPoint } from '../../components/SweepChart';

import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';
const DATA_SERVER = '\\\\crcv03a-cifs.cr.intel.com\\mfg_tlo_001\\DebugFramework';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

const CONTENT_OPTIONS = ['Dragon', 'DBM', 'Pseudo Slice', 'Pseudo Mesh', 'EFI', 'Linux', 'TSL', 'Sandstone', 'Imunch', 'Python', 'Other'];
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
  merge:            boolean;
  mergeTag:         string;
  mergeOutputName:  string;
  generate:         boolean;
  reportTag:        string;
  checkLogging:     boolean;
  skipStrings:      string;
  dragonData:       boolean;
  coreData:         boolean;
  summaryTab:       boolean;
  overview:         boolean;
  outputName:       string;
  saveFolder:       string;
}

type InputMode = 'path' | 'zip';

interface FwSheetData {
  sheet: string;
  columns: string[];
  rows: (string | number | null)[][];
  total_rows: number;
}

function isSweepType(type: string) {
  return /voltage|frequency|freq|shmoo|sweep/i.test(type);
}

/** Try to detect sweep structure: numeric column headers → count PASS/FAIL per column. */
function buildSweepPoints(data: FwSheetData): SweepPoint[] | null {
  if (!data.columns.length || !data.rows.length) return null;
  const numericIdxs = data.columns
    .map((c, i) => ({ c, i }))
    .filter(({ c }) => c !== '' && !isNaN(Number(c)) && isFinite(Number(c)))
    .map(({ i }) => i);
  if (numericIdxs.length < 2) return null;
  return numericIdxs.map(ci => {
    let pass = 0, fail = 0;
    data.rows.forEach(row => {
      const v = String(row[ci] ?? '').trim().toUpperCase();
      if (v === 'P' || v === 'PASS' || v === '1') pass++;
      else if (v === 'F' || v === 'FAIL' || v === '0') fail++;
    });
    return { x: data.columns[ci], pass, fail };
  });
}

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
  const [saving,     setSaving]     = useState(false);
  const [log,        setLog]        = useState('');

  // Charts state
  const [showFwCharts,    setShowFwCharts]    = useState(false);
  const [chartExpFilter,  setChartExpFilter]  = useState<Set<string>>(new Set());
  const [fwSheetList,     setFwSheetList]     = useState<string[]>([]);
  const [fwSheetCache,    setFwSheetCache]    = useState<Record<string, FwSheetData>>({});
  const [fwChartsLoading, setFwChartsLoading] = useState(false);
  const [sweepSheet,      setSweepSheet]      = useState('');
  const [reportToken, setReportToken] = useState('');
  const [pendingDownload, setPendingDownload] = useState<{blob: Blob; name: string} | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  const [opts, setOpts] = useState<ReportOptions>({
    merge: true, mergeTag: '', mergeOutputName: 'MergedSummary',
    generate: true, reportTag: '',
    checkLogging: true, skipStrings: '', dragonData: true,
    coreData: true, summaryTab: true, overview: false,
    outputName: 'FrameworkReport', saveFolder: '',
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

  // Auto-set folder path and output names when VID is selected
  useEffect(() => {
    if (vid) {
      setFolderPath(`${DATA_SERVER}\\${product}\\${vid}`);
      setOpts(o => ({
        ...o,
        outputName: `${vid}_FrameworkReport`,
        mergeOutputName: `${vid}_MergedSummary`,
      }));
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
        const details: {name: string; content: string; type: string; comments: string; include?: boolean; otherType?: string}[] =
          data.details ?? [];
        const names: string[] = data.experiments ?? details.map((d: {name: string}) => d.name);
        setExps((details.length > 0 ? details : names.map(n => ({ name: n, content: 'Dragon', type: 'Baseline', comments: '', include: true, otherType: '' })))
          .map(d => ({
            name: d.name, include: d.include ?? true,
            content: d.content || 'Dragon', type: d.type || 'Baseline',
            otherType: d.otherType || '', comments: d.comments || '',
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
        const details: {name: string; content: string; type: string; comments: string; include?: boolean; otherType?: string}[] =
          data.details ?? [];
        const names: string[] = data.experiments ?? details.map((d: {name: string}) => d.name) ?? Object.keys(data);
        setExps((details.length > 0 ? details : names.map(n => ({ name: n, content: 'Dragon', type: 'Baseline', comments: '', include: true, otherType: '' })))
          .map(d => ({
            name: d.name, include: d.include ?? true,
            content: d.content || 'Dragon', type: d.type || 'Baseline',
            otherType: d.otherType || '', comments: d.comments || '',
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

  const handleSaveConfig = async () => {
    const path = folderPath.trim();
    if (!path || inputMode !== 'path') {
      addLog('[WARN] Save Config is only available for network/server path mode.');
      return;
    }
    setSaving(true);
    try {
      const fd = new FormData();
      fd.append('folder_path', path);
      fd.append('experiments_json', JSON.stringify(exps));
      const resp = await fetch(`${BASE}/framework/save_config`, { method: 'POST', body: fd });
      if (!resp.ok) { addLog(`[ERROR] Save config: ${resp.status} ${await resp.text()}`); }
      else {
        const data = await resp.json();
        addLog(`[OK] Config saved (${data.count} experiments) → ${data.saved}`);
      }
    } catch (e: unknown) {
      addLog(`[ERROR] ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  // ── Chart effects and helpers ──────────────────────────────────────────

  // Load sheet list when charts are toggled on and a report token is available
  useEffect(() => {
    if (!showFwCharts || !reportToken) return;
    setFwChartsLoading(true);
    setFwSheetList([]);
    setFwSheetCache({});
    setSweepSheet('');
    fetch(`${BASE}/framework/sheets?token=${encodeURIComponent(reportToken)}`)
      .then(r => r.json())
      .then((d: Record<string, string[]>) => {
        const names: string[] = [];
        Object.values(d).forEach(arr => {
          if (Array.isArray(arr)) arr.forEach(n => { if (!names.includes(n)) names.push(n); });
        });
        setFwSheetList(names);
        if (names.length > 0) setSweepSheet(names[0]);
      })
      .catch(() => {})
      .finally(() => setFwChartsLoading(false));
  }, [showFwCharts, reportToken]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load a framework report sheet into cache
  const loadFwSheet = useCallback(async (sheet: string) => {
    if (fwSheetCache[sheet] || !reportToken) return;
    try {
      const r = await fetch(
        `${BASE}/framework/sheet_data?token=${encodeURIComponent(reportToken)}&sheet=${encodeURIComponent(sheet)}&max_rows=2000`,
      );
      const d: FwSheetData = await r.json();
      setFwSheetCache(prev => ({ ...prev, [sheet]: d }));
    } catch { /* swallow */ }
  }, [fwSheetCache, reportToken]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-load sheets that match selected (or all) experiments
  useEffect(() => {
    if (!showFwCharts || !fwSheetList.length) return;
    const expNames = new Set(
      chartExpFilter.size > 0
        ? Array.from(chartExpFilter)
        : exps.filter(e => e.include).map(e => e.name),
    );
    fwSheetList.forEach(s => {
      const matchesExp = expNames.has(s) || [...expNames].some(
        n => s.toLowerCase().includes(n.toLowerCase()) || n.toLowerCase().includes(s.toLowerCase()),
      );
      if (matchesExp) loadFwSheet(s);
    });
    // Also load the sweep-selected sheet
    if (sweepSheet) loadFwSheet(sweepSheet);
  }, [showFwCharts, fwSheetList, chartExpFilter, sweepSheet]); // eslint-disable-line react-hooks/exhaustive-deps

  // Pareto: row count per sheet that maps to an experiment
  const fwParetoData = useMemo<BarEntry[]>(() => {
    const expNames = new Set(
      chartExpFilter.size > 0
        ? Array.from(chartExpFilter)
        : exps.filter(e => e.include).map(e => e.name),
    );
    return fwSheetList
      .filter(s => fwSheetCache[s] && (
        expNames.has(s) ||
        [...expNames].some(n =>
          s.toLowerCase().includes(n.toLowerCase()) || n.toLowerCase().includes(s.toLowerCase()),
        )
      ))
      .map(s => ({ label: s, value: fwSheetCache[s].total_rows }))
      .sort((a, b) => b.value - a.value);
  }, [fwSheetList, fwSheetCache, chartExpFilter, exps]);

  // Sweep points for selected sheet
  const sweepPoints = useMemo<SweepPoint[] | null>(
    () => (sweepSheet && fwSheetCache[sweepSheet] ? buildSweepPoints(fwSheetCache[sweepSheet]) : null),
    [sweepSheet, fwSheetCache],
  );

  // Sweep-type experiments among included experiments
  const sweepExps = useMemo(
    () => exps.filter(e => e.include && isSweepType(e.type || e.otherType)),
    [exps],
  );

  function buildFormData(): FormData {
    const fd = new FormData();
    fd.append('experiments_json',  JSON.stringify(exps));
    fd.append('merge',             String(opts.merge));
    fd.append('merge_tag',         opts.mergeTag);
    fd.append('merge_output_name', opts.mergeOutputName);
    fd.append('generate',          String(opts.generate));
    fd.append('report_tag',        opts.reportTag);
    fd.append('check_logging',     String(opts.checkLogging));
    fd.append('skip_strings',      opts.skipStrings);
    fd.append('dragon_data',       String(opts.dragonData));
    fd.append('core_data',         String(opts.coreData));
    fd.append('summary_tab',       String(opts.summaryTab));
    fd.append('overview',          String(opts.overview));
    fd.append('output_name',       opts.outputName);
    return fd;
  }

  async function processResponse(resp: Response) {
    // Capture the preview token from response headers
    const token = resp.headers.get('X-Report-Token') ?? resp.headers.get('x-report-token') ?? '';
    if (token) setReportToken(token);

    const contentType = resp.headers.get('content-type') ?? '';
    const cd = resp.headers.get('content-disposition') ?? '';
    const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    const fname = match ? match[1].replace(/['"]/g, '') :
      (opts.merge && opts.generate ? `${opts.outputName}_files.zip`
        : opts.merge ? `${opts.mergeOutputName}.xlsx`
        : `${opts.outputName}.xlsx`);
    const blob = await resp.blob();
    setPendingDownload({ blob, name: fname });
    if (contentType.includes('zip') || fname.endsWith('.zip')) {
      addLog(`[OK] Report ready (ZIP with both files): ${fname} — click Download to save.`);
    } else {
      addLog(`[OK] Report ready: ${fname} — click Download to save.`);
    }
  }

  const handleGenerate = async () => {
    if (!opts.merge && !opts.generate) {
      addLog('[ERROR] No action selected — enable "Generate Report" and/or "Merge Summary".');
      return;
    }
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setGenerating(true);
    setReportToken('');
    setPendingDownload(null);
    addLog('[INFO] Generating report...');

    try {
      let resp: Response;
      if (inputMode === 'path') {
        const fd = buildFormData();
        fd.append('folder_path', folderPath);
        resp = await fetch(`${BASE}/framework/generate_from_path`, {
          method: 'POST', body: fd, signal: ctrl.signal,
        });
      } else {
        if (!zipFile) { addLog('[ERROR] ZIP file missing.'); setGenerating(false); return; }
        const fd = buildFormData();
        fd.append('zip_file', zipFile);
        resp = await fetch(`${BASE}/framework/generate`, {
          method: 'POST', body: fd, signal: ctrl.signal,
        });
      }
      if (!resp.ok) { addLog(`[ERROR] ${resp.status}: ${await resp.text()}`); }
      else { await processResponse(resp); }
    } catch (e: unknown) {
      if ((e as Error).name !== 'AbortError') addLog(`[ERROR] ${(e as Error).message}`);
      else addLog('[INFO] Cancelled.');
    } finally { setGenerating(false); abortRef.current = null; }
  };

  const handleSaveToFolder = async () => {
    if (!opts.merge && !opts.generate) {
      addLog('[ERROR] No action selected — enable "Generate Report" and/or "Merge Summary".');
      return;
    }
    let saveFolder = opts.saveFolder.trim();
    if (!saveFolder) {
      saveFolder = prompt('Enter destination folder path:') ?? '';
      if (!saveFolder) return;
      setOpt('saveFolder', saveFolder);
    }
    if (!folderPath) { addLog('[ERROR] No data folder path set.'); return; }
    setGenerating(true);
    addLog(`[INFO] Saving to ${saveFolder}...`);
    try {
      const resp = await fetch(`${BASE}/framework/save_to_folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          folder_path: folderPath, experiments: exps,
          merge: opts.merge, merge_tag: opts.mergeTag, merge_output_name: opts.mergeOutputName,
          generate: opts.generate, report_tag: opts.reportTag,
          check_logging: opts.checkLogging, skip_strings: opts.skipStrings,
          dragon_data: opts.dragonData, core_data: opts.coreData,
          summary_tab: opts.summaryTab, overview: opts.overview,
          output_name: opts.outputName, save_folder: saveFolder,
        }),
      });
      if (!resp.ok) { addLog(`[ERROR] ${resp.status}: ${await resp.text()}`); }
      else {
        const d = await resp.json();
        addLog(`[OK] Saved ${d.saved_files?.join(', ')} → ${d.folder}`);
      }
    } catch (e: unknown) {
      addLog(`[ERROR] ${(e as Error).message}`);
    } finally { setGenerating(false); }
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
              <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                <input
                  list="vid-list"
                  value={vid}
                  onChange={e => setVid(e.target.value)}
                  placeholder="Type or select a VID…"
                  style={{ flex: 1 }}
                />
                <datalist id="vid-list">
                  {vids.map(v => <option key={v} value={v} />)}
                </datalist>
                {vids.length > 0 &&
                  <span style={{ fontSize: 10, color: '#555', whiteSpace: 'nowrap' }}>
                    {vids.length} VIDs
                  </span>
                }
              </div>

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
              {inputMode === 'path' && (
                <button className="btn" onClick={handleSaveConfig} disabled={saving}>
                  {saving ? '⏳ Saving…' : '💾 Save Config'}
                </button>
              )}
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

      {/* Step 3: Report Options */}
      {parsed && (
        <div className="panel" style={{ marginBottom: 12 }}>
          <div className="section-title">Step 3 — Report Options</div>

          {/* Actions group */}
          <div className="opts-section-label">Actions</div>
          <div className="opts-grid">
            <label className="check-label">
              <input type="checkbox" checked={opts.merge} onChange={e => setOpt('merge', e.target.checked)} />
              Merge Summary
            </label>
            <span />

            <label className="check-label">
              <input type="checkbox" checked={opts.generate} onChange={e => setOpt('generate', e.target.checked)} />
              Generate Report
            </label>
            <span />

            <label className="check-label">
              <input type="checkbox" checked={opts.checkLogging} onChange={e => setOpt('checkLogging', e.target.checked)} />
              Check Logging
            </label>
            <input value={opts.skipStrings} onChange={e => setOpt('skipStrings', e.target.value)}
              placeholder="Skip strings (comma-sep)" disabled={!opts.checkLogging} />
          </div>

          {/* Extra sheets (only relevant when generate is on) */}
          <div className="opts-section-label" style={{ marginTop: 10 }}>Extra Sheets</div>
          <div className="opts-grid">
            <label className="check-label">
              <input type="checkbox" checked={opts.dragonData} onChange={e => setOpt('dragonData', e.target.checked)} />
              Dragon Data
            </label>
            <span />

            <label className="check-label">
              <input type="checkbox" checked={opts.coreData} onChange={e => setOpt('coreData', e.target.checked)} />
              Core Data
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
          </div>

          {/* Output file names */}
          <div className="opts-section-label" style={{ marginTop: 10 }}>Output File Names</div>
          <div className="opts-grid">
            <label>Report Name</label>
            <input value={opts.outputName} onChange={e => setOpt('outputName', e.target.value)}
              placeholder="{VID}_FrameworkReport" />
            <label>Merge Name</label>
            <input value={opts.mergeOutputName} onChange={e => setOpt('mergeOutputName', e.target.value)}
              placeholder="{VID}_MergedSummary" />
          </div>

          {/* Save to Folder (path mode only) */}
          {inputMode === 'path' && (
            <>
              <div className="opts-section-label" style={{ marginTop: 10 }}>Save to Folder</div>
              <div className="fr-save-bar">
                <input
                  className="fr-save-input"
                  value={opts.saveFolder}
                  onChange={e => setOpt('saveFolder', e.target.value)}
                  placeholder="Destination folder path (leave blank to prompt)"
                />
                <button
                  className="btn"
                  onClick={handleSaveToFolder}
                  disabled={generating}
                  title="Save file(s) directly to a folder on disk"
                >
                  💾 Save to Folder
                </button>
              </div>
            </>
          )}

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

      {/* Inline report viewer — shown after a successful generate */}
      {reportToken && (
        <div className="panel" style={{ marginTop: 12 }}>
          <div className="section-title-row">
            <span className="section-title" style={{ margin: 0, border: 0 }}>📊 Report Preview</span>
            {pendingDownload && (
              <button className="btn primary" onClick={() => downloadBlob(pendingDownload.blob, pendingDownload.name)}>
                ⬇ Download {pendingDownload.name}
              </button>
            )}
          </div>
          <ExcelViewer
            token={reportToken}
            apiBase={`${BASE}/framework`}
          />
        </div>
      )}

      {/* ── Charts section (optional, off by default) ─────────────────────── */}
      {reportToken && (
        <div className="panel" style={{ marginTop: 12 }}>
          <div className="section-title-row">
            <span className="section-title" style={{ margin: 0, border: 0 }}>📈 Charts</span>
            <label className="check-label" style={{ fontSize: 12 }}>
              <input
                type="checkbox"
                checked={showFwCharts}
                onChange={() => setShowFwCharts(v => !v)}
              />
              Show Charts
            </label>
          </div>

          {showFwCharts && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 10 }}>

              {/* Experiment filter */}
              {exps.length > 0 && (
                <div>
                  <div style={{ fontSize: 11, color: '#858585', marginBottom: 6 }}>Filter experiments for charts:</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {exps.filter(e => e.include).map(e => (
                      <label key={e.name} className="check-label" style={{ fontSize: 11 }}>
                        <input
                          type="checkbox"
                          checked={chartExpFilter.size === 0 || chartExpFilter.has(e.name)}
                          onChange={() => {
                            setChartExpFilter(prev => {
                              const next = new Set(prev.size === 0
                                ? exps.filter(x => x.include).map(x => x.name)
                                : Array.from(prev));
                              next.has(e.name) ? next.delete(e.name) : next.add(e.name);
                              // If all selected → reset to empty (means "all")
                              const allNames = exps.filter(x => x.include).map(x => x.name);
                              return next.size === allNames.length ? new Set() : next;
                            });
                          }}
                        />
                        {e.name} <span style={{ color: '#858585' }}>({e.type})</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Pareto */}
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#d4d4d4', marginBottom: 8 }}>
                  Pareto — Rows per Report Sheet
                </div>
                {fwChartsLoading && <div style={{ fontSize: 11, color: '#858585' }}>⏳ Loading chart data…</div>}
                {!fwChartsLoading && fwParetoData.length > 0 && (
                  <SimpleBarChart data={fwParetoData} />
                )}
                {!fwChartsLoading && fwParetoData.length === 0 && fwSheetList.length === 0 && (
                  <div style={{ fontSize: 11, color: '#858585' }}>No report sheets found — generate the report first.</div>
                )}
                {!fwChartsLoading && fwParetoData.length === 0 && fwSheetList.length > 0 && (
                  <div style={{ fontSize: 11, color: '#858585' }}>
                    No sheets matched selected experiments. Available sheets: {fwSheetList.join(', ')}.
                  </div>
                )}
              </div>

              {/* Sweep chart */}
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#d4d4d4', marginBottom: 8 }}>
                  Sweep Analysis
                  {sweepExps.length === 0 && (
                    <span style={{ fontSize: 10, fontWeight: 400, color: '#858585', marginLeft: 8 }}>
                      (no Voltage/Frequency/Shmoo experiments selected)
                    </span>
                  )}
                </div>

                {fwSheetList.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                    <span style={{ fontSize: 11, color: '#858585' }}>Sheet:</span>
                    <select
                      value={sweepSheet}
                      onChange={e => { setSweepSheet(e.target.value); loadFwSheet(e.target.value); }}
                      style={{ fontSize: 11 }}
                    >
                      {fwSheetList.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                )}

                {sweepSheet && fwSheetCache[sweepSheet] && sweepPoints && (
                  <SweepChart
                    data={sweepPoints}
                    title={`Sweep: ${sweepSheet}`}
                    xLabel="Parameter Value"
                  />
                )}
                {sweepSheet && fwSheetCache[sweepSheet] && !sweepPoints && (
                  <div style={{ fontSize: 11, color: '#858585' }}>
                    Sheet <em>{sweepSheet}</em> does not contain numeric column headers.
                    Sweep chart requires columns named with numeric parameter values (e.g. 800, 1000, 1200).
                  </div>
                )}
                {sweepSheet && !fwSheetCache[sweepSheet] && (
                  <div style={{ fontSize: 11, color: '#858585' }}>⏳ Loading sheet data…</div>
                )}
                {!sweepSheet && fwSheetList.length === 0 && (
                  <div style={{ fontSize: 11, color: '#858585' }}>Generate a report to enable sweep analysis.</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

