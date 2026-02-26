import React, { useState, useEffect } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

const PRODUCTS = ['GNR', 'GNR3', 'CWF', 'DMR'];
const OPERATIONS = ['8749', '8748', '8657', '7682', '7681', '7775'];
const YEARS = Array.from({ length: 7 }, (_, i) => new Date().getFullYear() - i + 1);
const WWS = Array.from({ length: 52 }, (_, i) => i + 1);

function currentWW(): number {
  const now = new Date();
  const start = new Date(now.getFullYear(), 0, 1);
  return Math.ceil(((now.getTime() - start.getTime()) / 86400000 + start.getDay() + 1) / 7);
}

export default function DPMBRequests() {
  const year = new Date().getFullYear();
  const ww = currentWW();

  const [vids,       setVids]       = useState('');
  const [user,       setUser]       = useState('');
  const [startYear,  setStartYear]  = useState(year);
  const [startWW,    setStartWW]    = useState(ww);
  const [endYear,    setEndYear]    = useState(year);
  const [endWW,      setEndWW]      = useState(ww);
  const [product,    setProduct]    = useState('GNR3');
  const [ops,        setOps]        = useState<string[]>([]);
  const [loading,    setLoading]    = useState(false);
  const [result,     setResult]     = useState('');
  const [resultType, setResultType] = useState<'ok' | 'err' | ''>('');

  // Auto-fill current user
  useEffect(() => {
    fetch(`${BASE}/dpmb/current-user`)
      .then(r => r.json())
      .then(d => { if (d.user) setUser(d.user); })
      .catch(() => {});
  }, []);

  const toggleOp = (op: string) =>
    setOps(prev => prev.includes(op) ? prev.filter(o => o !== op) : [...prev, op]);

  const handleSubmit = async () => {
    const vidList = vids.split(/[\n,]+/).map(v => v.trim()).filter(Boolean);
    if (!vidList.length) { setResult('⚠ No VIDs entered.'); setResultType('err'); return; }
    if (!ops.length)     { setResult('⚠ No operations selected.'); setResultType('err'); return; }

    setLoading(true);
    setResult('');
    setResultType('');
    try {
      const resp = await fetch(`${BASE}/dpmb/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vidlist: vidList,
          user,
          start_year: startYear,
          start_ww: startWW,
          end_year: endYear,
          end_ww: endWW,
          product,
          operations: ops,
        }),
      });
      const data = await resp.json();
      const text = JSON.stringify(data, null, 2);
      if (resp.ok) {
        setResult(`✅ Request submitted:\n${text}`);
        setResultType('ok');
      } else {
        setResult(`❌ Server error (${resp.status}):\n${text}`);
        setResultType('err');
      }
    } catch (e: any) {
      setResult(`❌ Network error: ${e.message}`);
      setResultType('err');
    } finally {
      setLoading(false);
    }
  };

  const handleStatus = async () => {
    setLoading(true);
    setResult('');
    setResultType('');
    try {
      const resp = await fetch(`${BASE}/dpmb/status?user=${encodeURIComponent(user)}&product=${product}`);
      const data = await resp.json();
      const text = JSON.stringify(data, null, 2);
      if (resp.ok) {
        setResult(`📋 Last job status:\n${text}`);
        setResultType('ok');
      } else {
        setResult(`❌ Server error (${resp.status}):\n${text}`);
        setResultType('err');
      }
    } catch (e: any) {
      setResult(`❌ Network error: ${e.message}`);
      setResultType('err');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tool-page dpmb-page">
      <h2 className="tool-title">DPMB Bucketer Requests</h2>
      <p className="tool-desc">Submit unit bucketer retest requests to the DPMB scheduling API.</p>

      <div className="dpmb-layout">
        {/* LEFT COLUMN */}
        <div className="dpmb-col">

          {/* Visual IDs */}
          <section className="dpmb-section">
            <h3 className="section-title">Visual IDs</h3>
            <label className="field-label">VID List (one per line or comma-separated)</label>
            <textarea
              className="dpmb-textarea"
              rows={8}
              placeholder={"D491916S00148\n75EH348100130\n..."}
              value={vids}
              onChange={e => setVids(e.target.value)}
            />
          </section>

          {/* User */}
          <section className="dpmb-section">
            <h3 className="section-title">User Configuration</h3>
            <label className="field-label">Intel Username</label>
            <input
              className="dpmb-input"
              type="text"
              value={user}
              onChange={e => setUser(e.target.value)}
              placeholder="your_user_id"
            />
          </section>

          {/* Time Range */}
          <section className="dpmb-section">
            <h3 className="section-title">Time Range</h3>
            <div className="dpmb-row">
              <div className="dpmb-field">
                <label className="field-label">Start Year</label>
                <select className="dpmb-select" value={startYear} onChange={e => setStartYear(+e.target.value)}>
                  {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div className="dpmb-field">
                <label className="field-label">Start WW</label>
                <select className="dpmb-select" value={startWW} onChange={e => setStartWW(+e.target.value)}>
                  {WWS.map(w => <option key={w} value={w}>WW{w}</option>)}
                </select>
              </div>
            </div>
            <div className="dpmb-row" style={{ marginTop: 8 }}>
              <div className="dpmb-field">
                <label className="field-label">End Year</label>
                <select className="dpmb-select" value={endYear} onChange={e => setEndYear(+e.target.value)}>
                  {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div className="dpmb-field">
                <label className="field-label">End WW</label>
                <select className="dpmb-select" value={endWW} onChange={e => setEndWW(+e.target.value)}>
                  {WWS.map(w => <option key={w} value={w}>WW{w}</option>)}
                </select>
              </div>
            </div>
          </section>
        </div>

        {/* RIGHT COLUMN */}
        <div className="dpmb-col">

          {/* Product + Operations */}
          <section className="dpmb-section">
            <h3 className="section-title">Request Configuration</h3>

            <label className="field-label">Product</label>
            <select className="dpmb-select" value={product} onChange={e => setProduct(e.target.value)}>
              {PRODUCTS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>

            <label className="field-label" style={{ marginTop: 14 }}>Operations (select one or more)</label>
            <div className="ops-list">
              {OPERATIONS.map(op => (
                <label key={op} className={`ops-item${ops.includes(op) ? ' selected' : ''}`}>
                  <input
                    type="checkbox"
                    checked={ops.includes(op)}
                    onChange={() => toggleOp(op)}
                  />
                  <span className="ops-code">{op}</span>
                </label>
              ))}
            </div>
          </section>

          {/* Buttons */}
          <div className="dpmb-buttons">
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? '⏳ Submitting…' : '📤 Submit Request'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={handleStatus}
              disabled={loading}
            >
              📋 Check Status
            </button>
          </div>

          {/* Result */}
          {result && (
            <pre className={`dpmb-result${resultType === 'err' ? ' error' : ' success'}`}>
              {result}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
