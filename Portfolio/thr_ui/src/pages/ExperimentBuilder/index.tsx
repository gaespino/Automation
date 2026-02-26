import React, { useState, useEffect, useRef } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

type ConfigValue = string | number | boolean | string[] | Record<string, unknown>;
type ConfigSchema = Record<string, ConfigValue>;

interface QueuedExperiment {
  id: number;
  name: string;
  fields: Record<string, string>;
}

function renderField(
  key: string,
  schema: ConfigValue,
  value: string,
  onChange: (v: string) => void,
) {
  if (Array.isArray(schema)) {
    return (
      <select value={value} onChange={e => onChange(e.target.value)}>
        {(schema as string[]).map(opt => <option key={String(opt)}>{String(opt)}</option>)}
      </select>
    );
  }
  if (typeof schema === 'boolean') {
    return (
      <label className="check-label">
        <input type="checkbox" checked={value === 'true'}
          onChange={e => onChange(String(e.target.checked))} />
        {key}
      </label>
    );
  }
  if (typeof schema === 'number') {
    return <input type="number" value={value} onChange={e => onChange(e.target.value)} />;
  }
  return <input value={value} onChange={e => onChange(e.target.value)} placeholder={String(schema)} />;
}

let nextId = 1;

export default function ExperimentBuilder() {
  const [products,  setProducts]  = useState<string[]>([]);
  const [product,   setProduct]   = useState('');
  const [schema,    setSchema]    = useState<ConfigSchema>({});
  const [form,      setForm]      = useState<Record<string, string>>({});
  const [expName,   setExpName]   = useState('');
  const [queue,     setQueue]     = useState<QueuedExperiment[]>([]);
  const [editId,    setEditId]    = useState<number | null>(null);
  const [filename,  setFilename]  = useState('experiments');
  const [loading,   setLoading]   = useState(false);
  const [saving,    setSaving]    = useState(false);
  const [error,     setError]     = useState('');
  const loadRef = useRef<HTMLInputElement>(null);

  // Load products on mount
  useEffect(() => {
    fetch(`${BASE}/experiments/products`)
      .then(r => r.json())
      .then(d => {
        const prods: string[] = d.products ?? [];
        setProducts(prods);
        if (prods.length) setProduct(prods[0]);
      })
      .catch(e => setError(e.message));
  }, []);

  // Load config when product changes
  useEffect(() => {
    if (!product) return;
    setLoading(true); setError('');
    fetch(`${BASE}/experiments/config/${product}`)
      .then(r => r.json())
      .then(d => {
        const cfg: ConfigSchema = d.config ?? {};
        setSchema(cfg);
        // Initialize form with defaults
        const defaults: Record<string, string> = {};
        for (const [k, v] of Object.entries(cfg)) {
          if (Array.isArray(v)) defaults[k] = String(v[0] ?? '');
          else if (typeof v === 'boolean') defaults[k] = String(v);
          else defaults[k] = String(v);
        }
        setForm(defaults);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [product]);

  const setField = (key: string, value: string) =>
    setForm(f => ({ ...f, [key]: value }));

  const addToQueue = () => {
    const name = expName.trim() || `Experiment_${nextId}`;
    if (editId !== null) {
      setQueue(q => q.map(e => e.id === editId ? { ...e, name, fields: { ...form } } : e));
      setEditId(null);
    } else {
      setQueue(q => [...q, { id: nextId++, name, fields: { ...form } }]);
    }
    setExpName('');
  };

  const startEdit = (exp: QueuedExperiment) => {
    setEditId(exp.id);
    setExpName(exp.name);
    setForm({ ...exp.fields });
  };

  const cancelEdit = () => { setEditId(null); setExpName(''); };

  const deleteFromQueue = (id: number) =>
    setQueue(q => q.filter(e => e.id !== id));

  const clearQueue = () => { setQueue([]); setEditId(null); };

  const handleSave = async () => {
    if (!queue.length) { setError('Queue is empty.'); return; }
    setSaving(true); setError('');
    try {
      const resp = await fetch(`${BASE}/experiments/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ experiments: queue, filename }),
      });
      if (!resp.ok) { setError(`${resp.status}: ${await resp.text()}`); }
      else {
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') ?? '';
        const match = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fname = match ? match[1].replace(/['"]/g, '') : `${filename}.tpl`;
        downloadBlob(blob, fname);
      }
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally { setSaving(false); }
  };

  const handleLoad = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        const data = JSON.parse(ev.target?.result as string);
        const loaded: QueuedExperiment[] = Array.isArray(data) ? data : (data.experiments ?? []);
        const reloaded = loaded.map(ex => ({ ...ex, id: nextId++ }));
        setQueue(reloaded);
      } catch { setError('Invalid .tpl file (expected JSON).'); }
    };
    reader.readAsText(f);
    e.target.value = '';
  };

  const schemaEntries = Object.entries(schema);

  return (
    <div className="tool-page">
      <h2 className="page-title">🧪 Experiment Builder</h2>

      <div className="eb-layout">
        {/* Left: Form */}
        <div>
          <div className="panel">
            <div className="section-title">Product</div>
            <select value={product} onChange={e => setProduct(e.target.value)} style={{ width: '100%' }}>
              {products.map(p => <option key={p}>{p}</option>)}
            </select>
            {loading && <div style={{ color: '#858585', fontSize: 11, marginTop: 6 }}>Loading config…</div>}
          </div>

          {schemaEntries.length > 0 && (
            <div className="panel" style={{ marginTop: 12 }}>
              <div className="section-title">Experiment Fields</div>
              <div style={{ marginBottom: 8 }}>
                <label style={{ display: 'block', marginBottom: 4 }}>Experiment Name</label>
                <input
                  value={expName}
                  onChange={e => setExpName(e.target.value)}
                  placeholder="e.g. V_Scan_0.8"
                  style={{ width: '100%' }}
                />
              </div>
              <div className="schema-form">
                {schemaEntries.map(([key, schemaVal]) => (
                  <React.Fragment key={key}>
                    <label title={key}>{key}</label>
                    <div>
                      {renderField(key, schemaVal, form[key] ?? '', v => setField(key, v))}
                    </div>
                  </React.Fragment>
                ))}
              </div>
              <div className="action-row" style={{ marginTop: 12 }}>
                <button className="btn primary" onClick={addToQueue}>
                  {editId !== null ? '✏ Update' : '+ Add to Queue'}
                </button>
                {editId !== null && (
                  <button className="btn" onClick={cancelEdit}>Cancel Edit</button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right: Queue */}
        <div>
          <div className="panel">
            <div className="section-title-row">
              <span className="section-title" style={{ margin: 0, border: 0 }}>
                Queue ({queue.length})
              </span>
              <div className="action-row">
                <button className="btn" onClick={clearQueue} disabled={!queue.length}>🗑 Clear</button>
              </div>
            </div>

            {queue.length === 0 ? (
              <div style={{ color: '#858585', fontSize: 12, marginTop: 8 }}>
                No experiments in queue. Add one from the form.
              </div>
            ) : (
              <div className="queue-table-wrap">
                <table className="queue-table">
                  <thead>
                    <tr><th>Experiment</th><th>Fields</th><th></th></tr>
                  </thead>
                  <tbody>
                    {queue.map(exp => (
                      <tr key={exp.id} className={editId === exp.id ? 'row-editing' : ''}>
                        <td className="q-name">{exp.name}</td>
                        <td className="q-fields">
                          {Object.entries(exp.fields).slice(0, 3).map(([k, v]) => (
                            <span key={k} className="field-tag">{k}={v}</span>
                          ))}
                          {Object.keys(exp.fields).length > 3 && (
                            <span className="field-more">+{Object.keys(exp.fields).length - 3}</span>
                          )}
                        </td>
                        <td className="q-actions">
                          <button className="btn" title="Edit" onClick={() => startEdit(exp)}>✏</button>
                          <button className="btn danger" title="Delete" onClick={() => deleteFromQueue(exp.id)}>🗑</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="panel" style={{ marginTop: 12 }}>
            <div className="section-title">Export / Import</div>
            <div className="form-grid" style={{ marginBottom: 10 }}>
              <label>Filename</label>
              <input value={filename} onChange={e => setFilename(e.target.value)} placeholder="experiments" />
            </div>
            {error && <div className="error-msg" style={{ marginBottom: 8 }}>{error}</div>}
            <div className="action-row">
              <button className="btn primary" onClick={handleSave} disabled={saving || !queue.length}>
                {saving ? '⏳ Saving…' : '⬇ Save .tpl'}
              </button>
              <button className="btn" onClick={() => loadRef.current?.click()}>
                📂 Load .tpl
              </button>
              <input ref={loadRef} type="file" accept=".tpl,.json" style={{ display: 'none' }} onChange={handleLoad} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
