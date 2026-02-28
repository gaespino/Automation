import React, { useState } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

const BANK_INSTANCES: Record<string, string[]> = {
  'CHA/CCF': [],
  LLC:     [],
  CORE:    ['ML2','DCU','IFU','DTLB'],
  MEM:     ['B2CMI','MSE','MCCHAN'],
  IO:      ['UBOX','UPI','ULA'],
  PORTIDS: [],
};

// Only show registers that the backend actually decodes for each bank
// (matches original PPV MCADecoder.py register definitions)
const BANK_REGS: Record<string, string[]> = {
  'CHA/CCF': ['MC_STATUS', 'MC_ADDR', 'MC_MISC', 'MC_MISC3'],
  LLC:       ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
  CORE:      ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
  MEM:       ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
  IO:        ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
  PORTIDS:   ['MCERRLOGGINGREG', 'IERRLOGGINGREG'],
};

// Map display register names to DecodeRequest field names
const REG_API_FIELD: Record<string, string> = {
  'MC_STATUS':        'mc_status',
  'MC_ADDR':          'mc_addr',
  'MC_MISC':          'mc_misc',
  'MC_MISC3':         'mc_misc3',
  'MCERRLOGGINGREG':  'mc_status',
  'IERRLOGGINGREG':   'mc_misc',
};

// Map frontend bank name to API bank value
const BANK_API_NAME: Record<string, string> = { 'CHA/CCF': 'CHA' };

const BANKS = Object.keys(BANK_INSTANCES);

interface ApiResponse { product: string; bank: string; results: Record<string, unknown>; }

function downloadBlob(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

/** Flatten results — arrays expand to indexed sub-rows, nested dicts to sub-keys. */
function flattenResults(results: Record<string, unknown>): Array<[string, string]> {
  const rows: Array<[string, string]> = [];
  for (const [key, val] of Object.entries(results)) {
    if (Array.isArray(val)) {
      val.forEach((v, i) => rows.push([`${key} [${i}]`, String(v ?? '')] ));
    } else if (val !== null && typeof val === 'object') {
      for (const [subk, subv] of Object.entries(val as Record<string, unknown>)) {
        rows.push([`${key} – ${subk}`, String(subv ?? '')]);
      }
    } else {
      rows.push([key, String(val ?? '')]);
    }
  }
  return rows;
}

export default function MCADecoder() {
  const [product,   setProduct]   = useState('GNR');
  const [bank,      setBank]      = useState('CORE');
  const [instance,  setInstance]  = useState('ML2');
  const [regs,      setRegs]      = useState<Record<string, string>>({});
  const [result,    setResult]    = useState<ApiResponse | null>(null);
  const [error,     setError]     = useState('');
  const [loading,   setLoading]   = useState(false);

  const instances = BANK_INSTANCES[bank] ?? [];
  const visibleRegs = BANK_REGS[bank] ?? Object.keys(BANK_REGS);

  const handleBankChange = (b: string) => {
    setBank(b);
    const inst = BANK_INSTANCES[b];
    setInstance(inst.length ? inst[0] : '');
  };

  const setReg = (key: string, val: string) =>
    setRegs(r => ({ ...r, [key]: val }));

  const handleDecode = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const apiBank = BANK_API_NAME[bank] ?? bank;
      const payload: Record<string, string | undefined> = {
        product, bank: apiBank,
        instance: instance || undefined,
      };
      for (const reg of (BANK_REGS[bank] ?? [])) {
        const field = REG_API_FIELD[reg] ?? reg.toLowerCase().replace(/ /g, '_');
        payload[field] = regs[reg] || undefined;
      }
      const resp = await fetch(`${BASE}/mca/decode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) { const t = await resp.text(); setError(`${resp.status}: ${t}`); }
      else { setResult(await resp.json()); }
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleExportTxt = () => {
    if (!result) return;
    const lines = flattenResults(result.results).map(([k, v]) => `${k}: ${v}`);
    downloadBlob(lines.join('\n'), 'mca_decode.txt', 'text/plain');
  };

  const handleExportCsv = () => {
    if (!result) return;
    const rows = flattenResults(result.results);
    const csv = ['Field,Value', ...rows.map(([k, v]) => `"${k}","${v.replace(/"/g, '""')}"`)].join('\n');
    downloadBlob(csv, 'mca_decode.csv', 'text/csv');
  };

  const renderResult = () => {
    if (!result) return null;
    const rows = flattenResults(result.results);
    if (rows.length === 0)
      return <div style={{ color: '#858585', fontSize: 12 }}>No decoded data returned.</div>;
    return (
      <table className="result-table">
        <thead>
          <tr><th>Field</th><th>Value</th></tr>
        </thead>
        <tbody>
          {rows.map(([k, v], i) => (
            <tr key={i}>
              <td className="field-key">{k}</td>
              <td className="field-val">{v}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  return (
    <div className="tool-page">
      <h2 className="page-title">🔍 MCA Decoder</h2>

      <div className="decoder-layout">
        <div className="panel">
          <div className="section-title">Configuration</div>
          <div className="form-grid">
            <label>Product</label>
            <select value={product} onChange={e => setProduct(e.target.value)}>
              {['GNR','CWF','DMR'].map(p => <option key={p}>{p}</option>)}
            </select>

            <label>Bank</label>
            <select value={bank} onChange={e => handleBankChange(e.target.value)}>
              {BANKS.map(b => <option key={b}>{b}</option>)}
            </select>

            {instances.length > 0 && <>
              <label>Instance</label>
              <select value={instance} onChange={e => setInstance(e.target.value)}>
                {instances.map(i => <option key={i}>{i}</option>)}
              </select>
            </>}
          </div>

          <div className="section-title" style={{ marginTop: 12 }}>
            Registers (hex)
            {bank === 'PORTIDS' && <span className="bank-hint"> — UBox registers (MCERRLOGGINGREG / IERRLOGGINGREG)</span>}
            {bank === 'CHA/CCF' && <span className="bank-hint"> — CHA (GNR/CWF) / CCF (DMR)</span>}
          </div>
          <div className="form-grid">
            {visibleRegs.map(reg => (
              <React.Fragment key={reg}>
                <label>{reg}</label>
                <input
                  value={regs[reg] ?? ''}
                  onChange={e => setReg(reg, e.target.value)}
                  placeholder="0x0000000000000000"
                  style={{ fontFamily: 'Consolas, monospace' }}
                />
              </React.Fragment>
            ))}
          </div>

          <div className="action-row" style={{ marginTop: 14 }}>
            <button className="btn primary" onClick={handleDecode} disabled={loading}>
              {loading ? '⏳ Decoding…' : '▶ Decode'}
            </button>
            {result && <>
              <button className="btn" onClick={handleExportTxt}>⬇ .txt</button>
              <button className="btn success" onClick={handleExportCsv}>⬇ .csv</button>
            </>}
          </div>
        </div>

        <div className="panel result-panel">
          <div className="section-title">Decode Results</div>
          {error && <div className="error-msg">{error}</div>}
          {!result && !error && <div style={{ color: '#858585', fontSize: 12 }}>Results will appear here after decoding.</div>}
          {result && renderResult()}
        </div>
      </div>
    </div>
  );
}
