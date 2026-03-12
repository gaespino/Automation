import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import ExcelViewer from '../../components/ExcelViewer';
import SimpleBarChart from '../../components/SimpleBarChart';
import type { BarEntry } from '../../components/SimpleBarChart';
import SweepChart from '../../components/SweepChart';
import type { SweepPoint } from '../../components/SweepChart';
import MCAPreview from '../MCAReport/MCAPreview';

import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';
const DATA_SERVER = '\\\\crcv03a-cifs.cr.intel.com\\mfg_tlo_001\\DebugFramework';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// MCA sheet detection — matches decoded tabs (CHA_MCAS, LLC_MCAS, CORE_MCAS, etc.)
function isMcaSheet(name: string) {
  return /_mca/i.test(name) || /^ubox/i.test(name) || /^mca_/i.test(name);
}

function findVidColFw(columns: string[]): number {
  const pats = [/visual.?id/i, /\bvid\b/i, /\bunit\b/i];
  for (const p of pats) {
    const idx = columns.findIndex(c => p.test(c));
    if (idx >= 0) return idx;
  }
  return -1;
}

// ── Heatmap SVG component (VID × MCA-tab fail-count matrix) ─────────────────
interface HeatmapFwProps { vids: string[]; sheets: string[]; matrix: number[][]; }
function HeatmapChartFw({ vids, sheets, matrix }: HeatmapFwProps) {
  const CW = 46; const CH = 18; const LW = 150; const HH = 64; const PAD = 10;
  const maxVal = Math.max(1, ...matrix.flat());
  const cellColor = (v: number) => {
    if (v === 0) return '#282828';
    const t = v / maxVal;
    return `rgb(${Math.round(90 + t * 134)},${Math.round(26 + t * 56)},${Math.round(26 + t * 56)})`;
  };
  const W = LW + sheets.length * CW + PAD;
  const H = HH + vids.length * CH + PAD + 28;
  return (
    <svg width={W} height={H} style={{ background: '#1e1e1e', display: 'block' }}>
      {sheets.map((s, si) => (
        <g key={s} transform={`translate(${LW + si * CW + CW / 2},${HH - 4})`}>
          <text transform="rotate(-45)" textAnchor="start"
            style={{ fontSize: 10, fill: '#bbb', fontFamily: 'monospace' }}>{s}</text>
        </g>
      ))}
      {vids.map((v, vi) => (
        <text key={v} x={LW - 6} y={HH + vi * CH + CH / 2 + 4} textAnchor="end"
          style={{ fontSize: 10, fill: '#aaa', fontFamily: 'monospace' }}>
          {v.length > 18 ? v.slice(0, 17) + '…' : v}
        </text>
      ))}
      {vids.map((v, vi) => sheets.map((s, si) => {
        const val = matrix[vi]?.[si] ?? 0;
        const x = LW + si * CW; const y = HH + vi * CH;
        return (
          <g key={`${vi}-${si}`}>
            <rect x={x} y={y} width={CW - 1} height={CH - 1} fill={cellColor(val)} rx={2} />
            {val > 0 && <text x={x + CW / 2} y={y + CH / 2 + 4} textAnchor="middle"
              style={{ fontSize: 9, fill: '#fff', fontFamily: 'monospace' }}>{val}</text>}
            <title>{v} — {s}: {val} fail{val !== 1 ? 's' : ''}</title>
          </g>
        );
      }))}
      {(() => {
        const ly = HH + vids.length * CH + 10; const sw = 26;
        return (
          <g>
            <text x={LW} y={ly + 10} style={{ fontSize: 9, fill: '#777', fontFamily: 'monospace' }}>0</text>
            {[1, 2, 3, 4, 5].map(i => (
              <g key={i} transform={`translate(${LW + 16 + (i - 1) * sw},${ly})`}>
                <rect width={sw - 1} height={12} fill={cellColor(Math.round(i / 5 * maxVal))} rx={2} />
                {i === 5 && <text x={sw / 2} y={22} textAnchor="middle"
                  style={{ fontSize: 9, fill: '#777', fontFamily: 'monospace' }}>{maxVal}</text>}
              </g>
            ))}
          </g>
        );
      })()}
    </svg>
  );
}

const CONTENT_OPTIONS = ['', 'Dragon', 'DBM', 'Pseudo Slice', 'Pseudo Mesh', 'EFI', 'Linux', 'TSL', 'Sandstone', 'Imunch', 'Python', 'Other'];
const TYPE_OPTIONS    = ['', 'Baseline', 'Loops', 'Voltage', 'Frequency', 'Shmoo', 'Sweep', 'Others', 'Invalid'];
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

/** Parse a Defeature cell value into { key → value } pairs.
 *  Input:  "CoreLicense::nan | IA::V0.05 | CFC::F16"
 *  Output: { CoreLicense: "nan", IA: "V0.05", CFC: "F16" }
 */
function parseDef(def: string): Record<string, string> {
  const parts: Record<string, string> = {};
  def.split('|').forEach(seg => {
    const m = seg.trim().match(/^([^:]+)::(.+)$/);
    if (m) parts[m[1].trim()] = m[2].trim();
  });
  return parts;
}

interface DefSweepSeries {
  key: string;    // e.g. "IA::V"
  label: string;  // e.g. "IA Voltage"
  points: SweepPoint[];
}

/** Build sweep series from Experiment_Report tab (Defeature + Status columns). */
function buildDefSweepSeries(data: FwSheetData, expFilter?: Set<string>): DefSweepSeries[] {
  if (!data.columns.length || !data.rows.length) return [];
  const defIdx    = data.columns.findIndex(c => /defeature/i.test(c));
  const statusIdx = data.columns.findIndex(c => /^status$/i.test(c));
  if (defIdx < 0 || statusIdx < 0) return [];
  const expColIdx = (expFilter?.size)
    ? data.columns.findIndex(c => /experiment|test.?name|test.?id/i.test(c))
    : -1;

  const seriesMap: Record<string, { label: string; vals: Record<string, { pass: number; fail: number }> }> = {};

  data.rows.forEach(row => {
    if (expFilter?.size && expColIdx >= 0) {
      const rowExp = String(row[expColIdx] ?? '').trim().toLowerCase();
      if (![...expFilter].some(e => e.toLowerCase() === rowExp)) return;
    }
    const def    = String(row[defIdx]    ?? '').trim();
    const status = String(row[statusIdx] ?? '').trim().toUpperCase();
    const isPas  = status === 'PASS' || status === 'P';
    const isFail = status === 'FAIL' || status === 'F';
    if (!isPas && !isFail) return;
    const parts = parseDef(def);
    Object.entries(parts).forEach(([ip, val]) => {
      if (!val || val.toLowerCase() === 'nan') return;
      let seriesKey: string;
      let seriesLabel: string;
      if (/^V[\d.]+$/i.test(val)) {
        seriesKey = `${ip}::V`; seriesLabel = `${ip} Voltage`;
      } else if (/^F[\d.]+$/i.test(val)) {
        seriesKey = `${ip}::F`; seriesLabel = `${ip} Frequency`;
      } else {
        seriesKey = ip; seriesLabel = ip;
      }
      if (!seriesMap[seriesKey]) seriesMap[seriesKey] = { label: seriesLabel, vals: {} };
      if (!seriesMap[seriesKey].vals[val]) seriesMap[seriesKey].vals[val] = { pass: 0, fail: 0 };
      if (isPas) seriesMap[seriesKey].vals[val].pass++;
      else       seriesMap[seriesKey].vals[val].fail++;
    });
  });

  return Object.entries(seriesMap).map(([key, { label, vals }]) => {
    const sorted = Object.entries(vals).sort((a, b) => {
      const nA = parseFloat(a[0].replace(/[^0-9.]/g, '')) || 0;
      const nB = parseFloat(b[0].replace(/[^0-9.]/g, '')) || 0;
      return nA - nB;
    });
    return { key, label, points: sorted.map(([x, { pass, fail }]) => ({ x, pass, fail })) };
  }).filter(s => s.points.length > 0);
}

/** Legacy: numeric column headers matrix format. */
function buildSweepPoints(data: FwSheetData): SweepPoint[] | null {
  if (!data.columns.length || !data.rows.length) return null;
  const numericIdxs = data.columns
    .map((c, i) => ({ c, i }))
    .filter(({ c }) => c !== '' && !isNaN(Number(c)) && isFinite(Number(c)))
    .map(({ i }) => i);
  if (numericIdxs.length >= 2) {
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
  const passIdx = data.columns.findIndex(c => /^pass(es)?$|^pass.?count$|^passing$/i.test(c));
  const failIdx = data.columns.findIndex(c => /^fail(s|ed)?$|^fail.?count$|^failing$/i.test(c));
  const paramIdx = data.columns.findIndex(c =>
    /param|freq|voltage|volt|speed|ratio|step|value|setting|point/i.test(c));
  if (passIdx >= 0 && failIdx >= 0 && data.rows.length >= 2) {
    const xIdx = paramIdx >= 0 ? paramIdx : 0;
    return data.rows.map(row => ({
      x: String(row[xIdx] ?? ''),
      pass: Number(row[passIdx] ?? 0) || 0,
      fail: Number(row[failIdx] ?? 0) || 0,
    }));
  }
  return null;
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
  const [generating,      setGenerating]      = useState(false);
  const [saving,          setSaving]          = useState(false);
  const [configTimestamp, setConfigTimestamp] = useState('');
  const [log,             setLog]             = useState('');

  // MCA rebuild state
  const [redoMca,         setRedoMca]         = useState(false);
  const [redoMcaAnalysis, setRedoMcaAnalysis] = useState(true);
  const [rebuildingMca,   setRebuildingMca]   = useState(false);
  const [mcaToken,        setMcaToken]        = useState('');
  const [mcaFilename,     setMcaFilename]     = useState('');
  const [mcaPendingDl,    setMcaPendingDl]    = useState<{blob: Blob; name: string} | null>(null);

  // Charts state
  const [showFwCharts,    setShowFwCharts]    = useState(false);
  const [chartExpFilter,  setChartExpFilter]  = useState<Set<string>>(new Set());
  const [pendingExpFilter, setPendingExpFilter] = useState<Set<string>>(new Set());
  const [fwSheetList,     setFwSheetList]     = useState<string[]>([]);
  const [fwFileSheets,    setFwFileSheets]    = useState<Record<string, string[]>>({});
  const [fwSheetCache,    setFwSheetCache]    = useState<Record<string, FwSheetData>>({});
  const [fwChartsLoading, setFwChartsLoading] = useState(false);
  const [sweepSheet,      setSweepSheet]      = useState('');
  const [selectedSweepKey,setSelectedSweepKey]= useState('');
  // MCA chart state — loaded from rebuild token
  const [showMcaCharts,     setShowMcaCharts]     = useState(false);
  const [selectedMcaChart,  setSelectedMcaChart]  = useState('__tabs__');
  const [mcaSheetCache,   setMcaSheetCache]   = useState<Record<string, FwSheetData>>({});
  const [mcaSheetsLoaded, setMcaSheetsLoaded] = useState<string[]>([]);
  const [mcaChartsLoading,setMcaChartsLoading]= useState(false);
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
        setExps((details.length > 0 ? details : names.map(n => ({ name: n, content: '', type: '', comments: '', include: true, otherType: '' })))
          .map(d => ({
            name: d.name, include: d.include ?? true,
            content: CONTENT_OPTIONS.includes(d.content ?? '') ? (d.content ?? '') : '',
            type:    TYPE_OPTIONS.includes(d.type ?? '')    ? (d.type ?? '')    : '',
            otherType: d.otherType || '', comments: d.comments || '',
          })));
        setConfigTimestamp(data.config_timestamp ?? '');
        // Restore saved opts if present
        if (data.opts && typeof data.opts === 'object' && Object.keys(data.opts).length > 0) {
          setOpts(prev => ({ ...prev, ...data.opts }));
        }
        setParsed(true);
        setChartExpFilter(new Set());
        setPendingExpFilter(new Set());
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
        setExps((details.length > 0 ? details : names.map(n => ({ name: n, content: '', type: '', comments: '', include: true, otherType: '' })))
          .map(d => ({
            name: d.name, include: d.include ?? true,
            content: CONTENT_OPTIONS.includes(d.content ?? '') ? (d.content ?? '') : '',
            type:    TYPE_OPTIONS.includes(d.type ?? '')    ? (d.type ?? '')    : '',
            otherType: d.otherType || '', comments: d.comments || '',
          })));
        setParsed(true);
        setChartExpFilter(new Set());
        setPendingExpFilter(new Set());
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
      fd.append('opts_json', JSON.stringify({
        merge: opts.merge, generate: opts.generate, checkLogging: opts.checkLogging,
        dragonData: opts.dragonData, coreData: opts.coreData, summaryTab: opts.summaryTab,
        overview: opts.overview, outputName: opts.outputName, mergeOutputName: opts.mergeOutputName,
        skipStrings: opts.skipStrings,
      }));
      const resp = await fetch(`${BASE}/framework/save_config`, { method: 'POST', body: fd });
      if (!resp.ok) { addLog(`[ERROR] Save config: ${resp.status} ${await resp.text()}`); }
      else {
        const data = await resp.json();
        setConfigTimestamp(data.timestamp ?? '');
        addLog(`[OK] Config saved (${data.count} experiments) → ${data.saved}`);
      }
    } catch (e: unknown) {
      addLog(`[ERROR] ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  // Saves config to the VID folder. Sends the timestamp loaded at scan time so the
  // backend can detect concurrent edits. If a conflict is found (409), asks the user
  // whether to overwrite before retrying with force=true.
  const autoSaveConfig = async (force = false): Promise<boolean> => {
    const path = folderPath.trim();
    if (!path || inputMode !== 'path') return true;
    try {
      const fd = new FormData();
      fd.append('folder_path', path);
      fd.append('experiments_json', JSON.stringify(exps));
      fd.append('opts_json', JSON.stringify({
        merge: opts.merge, generate: opts.generate, checkLogging: opts.checkLogging,
        dragonData: opts.dragonData, coreData: opts.coreData, summaryTab: opts.summaryTab,
        overview: opts.overview, outputName: opts.outputName, mergeOutputName: opts.mergeOutputName,
        skipStrings: opts.skipStrings,
      }));
      fd.append('expected_timestamp', configTimestamp);
      if (force) fd.append('force', 'true');
      const resp = await fetch(`${BASE}/framework/save_config`, { method: 'POST', body: fd });
      if (resp.status === 409) {
        const cdata = await resp.json();
        const ok = window.confirm(
          `Config was modified by another user at ${cdata.conflict_timestamp || 'unknown time'}.\n\nOverwrite with your current settings?`,
        );
        if (ok) return autoSaveConfig(true);
        addLog('[INFO] Config not saved — existing config kept.');
        return false;
      }
      if (!resp.ok) { addLog(`[WARN] Config auto-save failed: ${resp.status}`); return false; }
      const cdata = await resp.json();
      setConfigTimestamp(cdata.timestamp ?? '');
      addLog(`[OK] Config saved (${cdata.count} experiments) → ${cdata.saved}`);
      return true;
    } catch { return false; }
  };

  // ── Rebuild MCA ────────────────────────────────────────────────────────
  const handleRebuildMca = async () => {
    const tok = reportToken;
    // Find the merged file in the cached report sheets
    const mergedFilename = Object.keys(
      Object.fromEntries(Object.entries({}).concat(Object.entries({ ...{} })))
    )[0] ?? '';

    // Determine the filename: prefer the merge output name file
    const cacheFilename = opts.mergeOutputName
      ? `${opts.mergeOutputName}.xlsx`
      : `${opts.outputName}.xlsx`;

    if (!tok) { addLog('[ERROR] No report loaded — generate a report first.'); return; }
    setRebuildingMca(true);
    addLog(`[INFO] Rebuilding MCA tabs on ${mcaFilename || cacheFilename}…`);
    const targetFile = mcaFilename || cacheFilename;
    try {
      const fd = new FormData();
      fd.append('token',    tok);
      fd.append('filename', targetFile);
      fd.append('product',  product);
      fd.append('decode',   String(true));
      fd.append('analysis', String(redoMcaAnalysis));
      const resp = await fetch(`${BASE}/framework/rebuild_mca`, { method: 'POST', body: fd });
      if (!resp.ok) { addLog(`[ERROR] Rebuild MCA: ${resp.status}: ${await resp.text()}`); return; }
      const newToken = resp.headers.get('X-Report-Token') ?? resp.headers.get('x-report-token') ?? '';
      if (newToken) {
        setMcaToken(newToken);
        setMcaFilename(targetFile);
      }
      const blob = await resp.blob();
      setMcaPendingDl({ blob, name: targetFile });
      addLog(`[OK] MCA rebuild complete — ${targetFile}. Open 'MCA Charts' to analyse, or download.`);
      // Auto-show MCA charts
      setShowMcaCharts(true);
    } catch (e: unknown) {
      addLog(`[ERROR] ${(e as Error).message}`);
    } finally {
      setRebuildingMca(false);
    }
  };

  // Load MCA decoded sheets when MCA Charts panel is toggled on
  useEffect(() => {
    if (!showMcaCharts || !mcaToken) return;
    setMcaChartsLoading(true);
    setMcaSheetsLoaded([]);
    setMcaSheetCache({});
    fetch(`${BASE}/framework/sheets?token=${encodeURIComponent(mcaToken)}`)
      .then(r => r.json())
      .then((d: Record<string, string[]>) => {
        const names: string[] = [];
        Object.values(d).forEach(arr => {
          if (Array.isArray(arr)) arr.forEach(n => {
            if (!names.includes(n) && isMcaSheet(n)) names.push(n);
          });
        });
        setMcaSheetsLoaded(names);
        // Auto-load all MCA sheets
        names.forEach(s => {
          fetch(`${BASE}/framework/sheet_data?token=${encodeURIComponent(mcaToken)}&sheet=${encodeURIComponent(s)}&max_rows=5000`)
            .then(r => r.json())
            .then((sd: FwSheetData) => setMcaSheetCache(prev => ({ ...prev, [s]: sd })))
            .catch(() => {});
        });
      })
      .catch(() => {})
      .finally(() => setMcaChartsLoading(false));
  }, [showMcaCharts, mcaToken]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Chart effects and helpers ──────────────────────────────────────────

  // Load sheet list when charts are toggled on and a report token is available
  useEffect(() => {
    if (!showFwCharts || !reportToken) return;
    setFwChartsLoading(true);
    setFwSheetList([]);
    setFwSheetCache({});
    setFwFileSheets({});
    setSweepSheet('');
    fetch(`${BASE}/framework/sheets?token=${encodeURIComponent(reportToken)}`)
      .then(r => r.json())
      .then((d: Record<string, string[]>) => {
        setFwFileSheets(d);
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
  // ─ uses mergedSheets so pareto only addresses the merged summary file
  const mergedSheets = useMemo(() => {
    // Prefer the file with "merge" in its name (e.g. MergedSummary.xlsx)
    const mergedEntry = Object.entries(fwFileSheets).find(([f]) => /merge/i.test(f));
    if (mergedEntry) return mergedEntry[1];
    // Fall back to any "summary" file
    const summaryEntry = Object.entries(fwFileSheets).find(([f]) => /summary/i.test(f));
    if (summaryEntry) return summaryEntry[1];
    // Last resort: all sheets
    return fwSheetList;
  }, [fwFileSheets, fwSheetList]);

  useEffect(() => {
    if (!showFwCharts || !fwSheetList.length) return;
    const sheetsToLoad = mergedSheets.length > 0 ? mergedSheets : fwSheetList;
    const expNames = new Set<string>(
      chartExpFilter.size > 0
        ? Array.from(chartExpFilter)
        : exps.filter(e => e.include).map(e => e.name),
    );
    sheetsToLoad.forEach(s => {
      const matchesExp = expNames.has(s) || [...expNames].some(
        n => s.toLowerCase().includes(n.toLowerCase()) || n.toLowerCase().includes(s.toLowerCase()),
      );
      if (matchesExp) loadFwSheet(s);
    });
    // Also load the sweep-selected sheet + experiment report sheet
    if (sweepSheet) loadFwSheet(sweepSheet);
    // Auto-load Experiment_Report tab for Defeature sweep analysis
    const expReport = fwSheetList.find(s => /experiment.?report/i.test(s));
    if (expReport) loadFwSheet(expReport);
  }, [showFwCharts, fwSheetList, mergedSheets, chartExpFilter, sweepSheet]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-detect experiment report sheet for sweep
  const expReportSheet = useMemo(
    () => fwSheetList.find(s => /experiment.?report/i.test(s)) ?? '',
    [fwSheetList],
  );

  // Build Defeature sweep series from Experiment_Report tab
  const sweepSeries = useMemo<DefSweepSeries[]>(
    () => (expReportSheet && fwSheetCache[expReportSheet]
      ? buildDefSweepSeries(fwSheetCache[expReportSheet],
          chartExpFilter.size > 0 ? chartExpFilter : undefined)
      : []),
    [expReportSheet, fwSheetCache, chartExpFilter],
  );

  // Auto-select first series when series change
  useEffect(() => {
    if (sweepSeries.length > 0 && !sweepSeries.find(s => s.key === selectedSweepKey)) {
      setSelectedSweepKey(sweepSeries[0].key);
    }
  }, [sweepSeries]); // eslint-disable-line react-hooks/exhaustive-deps

  // Pareto: unique failing VIDs per experiment sheet in the merged file
  const fwParetoData = useMemo<BarEntry[]>(() => {
    const expNames = new Set<string>(
      chartExpFilter.size > 0
        ? Array.from(chartExpFilter)
        : exps.filter(e => e.include).map(e => e.name),
    );
    const sheets = mergedSheets.length > 0 ? mergedSheets : fwSheetList;
    return sheets
      .filter(s => fwSheetCache[s] && (
        expNames.has(s) ||
        [...expNames].some(n =>
          s.toLowerCase() === n.toLowerCase() ||
          s.toLowerCase().includes(n.toLowerCase()) ||
          n.toLowerCase().includes(s.toLowerCase()),
        )
      ))
      .map(s => {
        const d  = fwSheetCache[s];
        // Count unique VIDs; fall back to total_rows when no VID column found
        const vi = d.columns.findIndex(c => /visual.?id|\bvid\b|\bunit\b/i.test(c));
        const val = vi >= 0
          ? new Set(d.rows.map(r => r[vi]).filter(v => v != null && String(v).trim() !== '')).size
          : d.total_rows;
        return { label: s, value: val };
      })
      .filter(e => e.value > 0)
      .sort((a, b) => b.value - a.value);
  }, [mergedSheets, fwSheetList, fwSheetCache, chartExpFilter, exps]);

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

  // ── MCA chart data memos (computed from decoded _MCAS sheets) ─────────

  // Fails per Tab: row-count per MCA sheet
  const mcaFailsPerTab = useMemo<BarEntry[]>(() => {
    return mcaSheetsLoaded
      .filter(s => mcaSheetCache[s])
      .map(s => ({ label: s, value: mcaSheetCache[s].total_rows }))
      .filter(e => e.value > 0)
      .sort((a, b) => b.value - a.value);
  }, [mcaSheetsLoaded, mcaSheetCache]);

  // Fails per VID: aggregate across all loaded MCA sheets
  const mcaFailsPerVid = useMemo<BarEntry[]>(() => {
    const counts: Record<string, number> = {};
    for (const s of mcaSheetsLoaded) {
      const d = mcaSheetCache[s];
      if (!d) continue;
      const vi = findVidColFw(d.columns);
      if (vi < 0) continue;
      d.rows.forEach(r => {
        const v = String(r[vi] ?? '').trim();
        if (v && v !== 'N/A' && v !== 'nan' && v !== 'None')
          counts[v] = (counts[v] ?? 0) + 1;
      });
    }
    return Object.entries(counts)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 50);
  }, [mcaSheetsLoaded, mcaSheetCache]);

  // Multi-IP heatmap: VIDs that fail in 2+ MCA tabs
  const mcaHeatmapData = useMemo(() => {
    const sheets = mcaSheetsLoaded.filter(s => mcaSheetCache[s]);
    const vidSheetCounts: Record<string, Record<string, number>> = {};
    for (const s of sheets) {
      const d = mcaSheetCache[s];
      if (!d) continue;
      const vi = findVidColFw(d.columns);
      if (vi < 0) continue;
      d.rows.forEach(r => {
        const v = String(r[vi] ?? '').trim();
        if (v && v !== 'N/A' && v !== 'nan' && v !== 'None')
          (vidSheetCounts[v] ??= {})[s] = (vidSheetCounts[v][s] ?? 0) + 1;
      });
    }
    const multiVids = Object.entries(vidSheetCounts)
      .filter(([, sc]) => Object.keys(sc).length >= 2)
      .sort((a, b) => Object.keys(b[1]).length - Object.keys(a[1]).length
                   || Object.values(b[1]).reduce((x, y) => x + y, 0)
                   - Object.values(a[1]).reduce((x, y) => x + y, 0))
      .slice(0, 40)
      .map(([v]) => v);
    const matrix = multiVids.map(v => sheets.map(s => vidSheetCounts[v]?.[s] ?? 0));
    return { vids: multiVids, sheets, matrix };
  }, [mcaSheetsLoaded, mcaSheetCache]);

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
      else {
        await processResponse(resp);
        // Auto-save config after every successful generate so field values are persisted
        if (inputMode === 'path') await autoSaveConfig();
      }
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
                        {CONTENT_OPTIONS.map(c => <option key={c} value={c}>{c === '' ? '— unset —' : c}</option>)}
                      </select>
                    </td>
                    <td>
                      <select value={exp.type} onChange={e => updateExp(i, 'type', e.target.value)}>
                        {TYPE_OPTIONS.map(t => <option key={t} value={t}>{t === '' ? '— unset —' : t}</option>)}
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

          {/* Redo MCA Analysis (requires Merge Summary) */}
          <div className="opts-section-label" style={{ marginTop: 10 }}>MCA Analysis</div>
          <div className="opts-grid">
            <label className="check-label" title="After merging, re-run the MCA decoder and Analysis on the merged file (requires CHA + CORE tabs)">
              <input type="checkbox" checked={redoMca} onChange={e => setRedoMca(e.target.checked)}
                disabled={!opts.merge} />
              Redo MCA Analysis
            </label>
            <span style={{ fontSize: 10, color: '#777' }}>
              Re-decodes + rebuilds CHA_MCAS, LLC_MCAS, CORE_MCAS, IO_MCAS, UBOX from merged file
            </span>

            <label className="check-label" style={{ paddingLeft: 16 }}
              title="Also run MCAAnalyzer to generate the Analysis sheet">
              <input type="checkbox" checked={redoMcaAnalysis} onChange={e => setRedoMcaAnalysis(e.target.checked)}
                disabled={!redoMca || !opts.merge} />
              Include MCA Analysis sheet
            </label>
            <span />
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

          {/* Rebuild MCA — shown after a report has been generated */}
          {reportToken && (
            <div className="action-row" style={{ marginTop: 8, flexWrap: 'wrap', gap: 8 }}>
              <button
                className="btn"
                style={{ background: '#5a2d82', borderColor: '#7a3daa', color: '#fff' }}
                onClick={handleRebuildMca}
                disabled={rebuildingMca}
                title="Rebuild MCA decoded tabs (CHA_MCAS, LLC_MCAS, CORE_MCAS, etc.) from CHA + CORE data in the merged file"
              >
                {rebuildingMca ? '⏳ Rebuilding MCA…' : '🔬 Rebuild MCA Tabs'}
              </button>
              {mcaPendingDl && (
                <button className="btn" onClick={() => downloadBlob(mcaPendingDl.blob, mcaPendingDl.name)}>
                  ⬇ {mcaPendingDl.name}
                </button>
              )}
            </div>
          )}
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
            sheetFilter={(name: string) =>
              !/^(cha|ccf|core|ppv|mem|io|dmi|upi|hbm)\s*$/i.test(name) && !isMcaSheet(name)
            }
          />
        </div>
      )}

      {/* ── Sweep Charts section (Voltage / Frequency experiments only) ────── */}
      {reportToken && (
        <div className="panel" style={{ marginTop: 12 }}>
          <div className="section-title-row">
            <span className="section-title" style={{ margin: 0, border: 0 }}>📈 Sweep Charts</span>
            <label className="check-label" style={{ fontSize: 12 }}>
              <input
                type="checkbox"
                checked={showFwCharts}
                onChange={() => setShowFwCharts(v => !v)}
              />
              Show Charts
            </label>
          </div>

          {/* Experiment filter — always visible, affects both charts and MCA analysis */}
          {exps.filter(e => e.include).length > 1 && (
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginTop: 8, paddingBottom: 8, borderBottom: '1px solid #2e2e2e' }}>
              <div style={{ flex: 1, display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 11, color: '#858585', whiteSpace: 'nowrap' }}>Experiments:</span>
                {exps.filter(e => e.include).map(e => (
                  <label key={e.name} className="check-label" style={{ fontSize: 11 }}>
                    <input
                      type="checkbox"
                      checked={pendingExpFilter.size === 0 || pendingExpFilter.has(e.name)}
                      onChange={() => {
                        setPendingExpFilter(prev => {
                          const next = new Set(prev.size === 0
                            ? exps.filter(x => x.include).map(x => x.name)
                            : Array.from(prev));
                          next.has(e.name) ? next.delete(e.name) : next.add(e.name);
                          const allNames = exps.filter(x => x.include).map(x => x.name);
                          return next.size === allNames.length ? new Set() : next;
                        });
                      }}
                    />
                    {e.name} <span style={{ color: '#858585' }}>({e.type || '—'})</span>
                  </label>
                ))}
              </div>
              <button
                className={`btn${(pendingExpFilter.size !== chartExpFilter.size || [...pendingExpFilter].some(n => !chartExpFilter.has(n))) ? ' primary' : ''}`}
                onClick={() => setChartExpFilter(new Set(pendingExpFilter))}
                style={{ flexShrink: 0, fontSize: 11 }}
                title="Apply experiment filter to charts and MCA analysis"
              >
                🔁 Apply
              </button>
            </div>
          )}

          {showFwCharts && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 10 }}>

              {/* Sweep / Defeature Analysis */}
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#d4d4d4', marginBottom: 8 }}>
                  Sweep / Defeature Analysis
                </div>

                {/* Defeature mode — Experiment_Report tab with Defeature + Status columns */}
                {expReportSheet && sweepSeries.length > 0 && (
                  <>
                    <div style={{ fontSize: 11, color: '#858585', marginBottom: 8 }}>
                      Source: <em>{expReportSheet}</em> — {sweepSeries.length} sweep parameter{sweepSeries.length !== 1 ? 's' : ''} detected
                    </div>
                    {/* Series selector buttons */}
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 10 }}>
                      {sweepSeries.map(s => {
                        const sel = selectedSweepKey === s.key;
                        return (
                          <button key={s.key} onClick={() => setSelectedSweepKey(s.key)}
                            style={{
                              fontSize: 11, padding: '2px 10px', borderRadius: 3, border: '1px solid',
                              cursor: 'pointer',
                              background: sel ? '#0078d4' : 'transparent',
                              borderColor: sel ? '#0078d4' : '#555',
                              color: sel ? '#fff' : 'inherit',
                            }}>
                            {s.label}
                          </button>
                        );
                      })}
                    </div>
                    {sweepSeries.filter(s => s.key === selectedSweepKey).map(s => (
                      <SweepChart
                        key={s.key}
                        data={s.points}
                        title={s.label}
                        xLabel={/::V/i.test(s.key) ? 'Voltage (V)' : /::F/i.test(s.key) ? 'Frequency (GHz)' : 'Value'}
                      />
                    ))}
                  </>
                )}

                {/* Fallback: auto-detect numeric headers or manual sheet picker */}
                {(!expReportSheet || sweepSeries.length === 0) && (
                  <>
                    {expReportSheet && fwSheetCache[expReportSheet] && sweepSeries.length === 0 && (
                      <div style={{ fontSize: 11, color: '#858585', marginBottom: 8 }}>
                        <em>{expReportSheet}</em> found but no Defeature/Status columns detected. Using manual mode.
                      </div>
                    )}
                    {fwSheetList.length > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                        <span style={{ fontSize: 11, color: '#858585' }}>Sheet:</span>
                        <select value={sweepSheet}
                          onChange={e => { setSweepSheet(e.target.value); loadFwSheet(e.target.value); }}
                          style={{ fontSize: 11 }}>
                          {(mergedSheets.length > 0 ? mergedSheets : fwSheetList).map(s => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>
                      </div>
                    )}
                    {sweepSheet && fwSheetCache[sweepSheet] && (() => {
                      const pts = buildSweepPoints(fwSheetCache[sweepSheet]);
                      return pts
                        ? <SweepChart data={pts} title={`Sweep: ${sweepSheet}`} xLabel="Parameter Value" />
                        : <div style={{ fontSize: 11, color: '#858585' }}>
                            Sheet <em>{sweepSheet}</em> has no numeric column headers or PASS/FAIL count columns.
                          </div>;
                    })()}
                    {sweepSheet && !fwSheetCache[sweepSheet] && (
                      <div style={{ fontSize: 11, color: '#858585' }}>⏳ Loading sheet data…</div>
                    )}
                    {!sweepSheet && fwSheetList.length === 0 && (
                      <div style={{ fontSize: 11, color: '#858585' }}>Generate a report to enable sweep analysis.</div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}
      {/* ── MCA Analysis section — reuses MCAPreview from MCA Report ─────── */}
      {mcaToken && (
        <div className="panel" style={{ marginTop: 12 }}>
          <div className="section-title">🔬 MCA Analysis</div>
          <MCAPreview
            token={mcaToken}
            apiBase={`${BASE}/framework`}
            expFilter={
              chartExpFilter.size > 0
                ? Array.from(chartExpFilter)
                : exps.filter(e => e.include).map(e => e.name)
            }
          />
        </div>
      )}
    </div>
  );
}

