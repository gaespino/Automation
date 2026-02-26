import React, { useState } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

const BANK_INSTANCES: Record<string, string[]> = {
  CHA:     [],
  CORE:    ['ML2','DCU','IFU','DTLB','L2'],
  MEM:     ['B2CMI','MSE','MCCHAN'],
  IO:      ['UBOX','UPI','ULA'],
  PORTIDS: [],
};
const BANKS = Object.keys(BANK_INSTANCES);

interface DecodeResult {
  [key: string]: unknown;
}

function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

export default function MCADecoder() {
  const [product,   setProduct]   = useState('GNR');
  const [bank,      setBank]      = useState('CORE');
  const [instance,  setInstance]  = useState('ML2');
  const [mcStatus,  setMcStatus]  = useState('');
  const [mcAddr,    setMcAddr]    = useState('');
  const [mcMisc,    setMcMisc]    = useState('');
  const [mcMisc2,   setMcMisc2]   = useState('');
  const [mcMisc3,   setMcMisc3]   = useState('');
  const [mcMisc4,   setMcMisc4]   = useState('');
  const [result,    setResult]    = useState<DecodeResult | null>(null);
  const [error,     setError]     = useState('');
  const [loading,   setLoading]   = useState(false);

  const instances = BANK_INSTANCES[bank] ?? [];

  const handleBankChange = (b: string) => {
    setBank(b);
    const inst = BANK_INSTANCES[b];
    setInstance(inst.length ? inst[0] : '');
  };

  const handleDecode = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const resp = await fetch(`${BASE}/mca/decode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product, bank,
          instance:  instance  !== '' ? instance  : undefined,
          mc_status: mcStatus  !== '' ? mcStatus  : undefined,
          mc_addr:   mcAddr    !== '' ? mcAddr    : undefined,
          mc_misc:   mcMisc    !== '' ? mcMisc    : undefined,
          mc_misc2:  mcMisc2   !== '' ? mcMisc2   : undefined,
          mc_misc3:  mcMisc3   !== '' ? mcMisc3   : undefined,
          mc_misc4:  mcMisc4   !== '' ? mcMisc4   : undefined,
        }),
      });
      if (!resp.ok) { const t = await resp.text(); setError(`${resp.status}: ${t}`); }
      else { setResult(await resp.json()); }
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    if (!result) return;
    const lines = Object.entries(result).map(([k, v]) => `${k}: ${JSON.stringify(v)}`);
    downloadText(lines.join('\n'), 'mca_decode.txt');
  };

  const renderResult = () => {
    if (!result) return null;
    const entries = Object.entries(result);
    return (
      <table className="result-table">
        <thead>
          <tr><th>Field</th><th>Value</th></tr>
        </thead>
        <tbody>
          {entries.map(([k, v]) => (
            <tr key={k}>
              <td className="field-key">{k}</td>
              <td className="field-val">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</td>
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

          <div className="section-title" style={{ marginTop: 12 }}>Registers (hex)</div>
          <div className="form-grid">
            {[
              ['MC_STATUS', mcStatus, setMcStatus],
              ['MC_ADDR',   mcAddr,   setMcAddr],
              ['MC_MISC',   mcMisc,   setMcMisc],
              ['MC_MISC2',  mcMisc2,  setMcMisc2],
              ['MC_MISC3',  mcMisc3,  setMcMisc3],
              ['MC_MISC4',  mcMisc4,  setMcMisc4],
            ].map(([lbl, val, setter]) => (
              <React.Fragment key={lbl as string}>
                <label>{lbl as string}</label>
                <input
                  value={val as string}
                  onChange={e => (setter as (v: string) => void)(e.target.value)}
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
            {result && (
              <button className="btn success" onClick={handleExport}>⬇ Export .txt</button>
            )}
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
