import React, { useState, useEffect, useRef } from 'react';
import './style.css';

const BASE = import.meta.env.VITE_API_BASE ?? '/api';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

interface FieldConfig {
  section?: string;
  type?: string;
  default?: string | number | boolean;
  description?: string;
  required?: boolean;
  options?: string[];
}

type FieldConfigs = Record<string, FieldConfig>;

interface QueuedExperiment {
  id: number;
  name: string;
  fields: Record<string, string>;
  dirty?: boolean;  // has unsaved changes
}

function buildDefaults(fieldConfigs: FieldConfigs): Record<string, string> {
  const defaults: Record<string, string> = {};
  for (const [k, cfg] of Object.entries(fieldConfigs)) {
    if (cfg.options && cfg.options.length > 0) {
      defaults[k] = String(cfg.options[0]);
    } else if (cfg.default !== undefined) {
      defaults[k] = String(cfg.default);
    } else {
      defaults[k] = '';
    }
  }
  return defaults;
}

function renderField(
  key: string,
  cfg: FieldConfig,
  value: string,
  onChange: (v: string) => void,
) {
  if (cfg.options && cfg.options.length > 0) {
    return (
      <select value={value} onChange={e => onChange(e.target.value)} title={cfg.description}>
        {cfg.options.map(opt => <option key={opt}>{opt}</option>)}
      </select>
    );
  }
  if (cfg.type === 'bool') {
    return (
      <label className="check-label" title={cfg.description}>
        <input type="checkbox" checked={value === 'true' || value === 'True'}
          onChange={e => onChange(String(e.target.checked))} />
        {key}
      </label>
    );
  }
  if (cfg.type === 'int' || cfg.type === 'float') {
    return (
      <input type="number" value={value}
        onChange={e => onChange(e.target.value)}
        title={cfg.description}
        placeholder={String(cfg.default ?? '')} />
    );
  }
  return (
    <input value={value}
      onChange={e => onChange(e.target.value)}
      title={cfg.description}
      placeholder={String(cfg.default ?? '')} />
  );
}

let nextId = 1;

export default function ExperimentBuilder() {
  const [products,     setProducts]     = useState<string[]>([]);
  const [product,      setProduct]      = useState('');
  const [fieldConfigs, setFieldConfigs] = useState<FieldConfigs>({});
  const [form,         setForm]         = useState<Record<string, string>>({});
  const [expName,      setExpName]      = useState('');
  const [queue,        setQueue]        = useState<QueuedExperiment[]>([]);
  const [editId,       setEditId]       = useState<number | null>(null);
  const [filename,     setFilename]     = useState('experiments');
  const [loading,      setLoading]      = useState(false);
  const [saving,       setSaving]       = useState(false);
  const [error,        setError]        = useState('');
  const [formDirty,    setFormDirty]    = useState(false);
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
        const fc: FieldConfigs = d.field_configs ?? {};
        setFieldConfigs(fc);
        setForm(buildDefaults(fc));
        setFormDirty(false);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [product]);

  const setField = (key: string, value: string) => {
    setForm(f => ({ ...f, [key]: value }));
    setFormDirty(true);
  };

  // Group fields by section
  const sectionGroups = React.useMemo(() => {
    const groups: Record<string, [string, FieldConfig][]> = {};
    for (const [k, cfg] of Object.entries(fieldConfigs)) {
      const sec = cfg.section ?? 'General';
      if (!groups[sec]) groups[sec] = [];
      groups[sec].push([k, cfg]);
    }
    return groups;
  }, [fieldConfigs]);

  const addToQueue = () => {
    const name = expName.trim() || `Experiment_${nextId}`;
    if (editId !== null) {
      setQueue(q => q.map(e => e.id === editId
        ? { ...e, name, fields: { ...form }, dirty: false } : e));
      setEditId(null);
    } else {
      setQueue(q => [...q, { id: nextId++, name, fields: { ...form }, dirty: false }]);
    }
    setExpName('');
    setFormDirty(false);
  };

  const startEdit = (exp: QueuedExperiment) => {
    setEditId(exp.id);
    setExpName(exp.name);
    setForm({ ...exp.fields });
    setFormDirty(false);
  };

  const duplicateExp = (exp: QueuedExperiment) => {
    const newExp: QueuedExperiment = {
      id: nextId++,
      name: `${exp.name}_copy`,
      fields: { ...exp.fields },
      dirty: false,
    };
    setQueue(q => [...q, newExp]);
  };

  const cancelEdit = () => {
    setEditId(null);
    setExpName('');
    setForm(buildDefaults(fieldConfigs));
    setFormDirty(false);
  };

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
        // Mark all as saved
        setQueue(q => q.map(e => ({ ...e, dirty: false })));
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
        const reloaded = loaded.map(ex => ({ ...ex, id: nextId++, dirty: false }));
        setQueue(reloaded);
      } catch { setError('Invalid .tpl file (expected JSON).'); }
    };
    reader.readAsText(f);
    e.target.value = '';
  };

  return (
    <div className="tool-page">
      <h2 className="page-title">🧪 Experiment Builder</h2>

      <div className="eb-layout">
        {/* ─── Left: Form ─────────────────────────────────────────── */}
        <div>
          <div className="panel">
            <div className="section-title">Product</div>
            <select value={product} onChange={e => setProduct(e.target.value)} style={{ width: '100%' }}>
              {products.map(p => <option key={p}>{p}</option>)}
            </select>
            {loading && <div style={{ color: '#858585', fontSize: 11, marginTop: 6 }}>Loading config…</div>}
          </div>

          {Object.keys(fieldConfigs).length > 0 && (
            <div className="panel" style={{ marginTop: 12 }}>
              <div className="section-title">
                Experiment Fields
                {formDirty && <span className="dirty-badge" title="Unsaved changes"> ●</span>}
              </div>

              <div style={{ marginBottom: 8 }}>
                <label style={{ display: 'block', marginBottom: 4 }}>Experiment Name</label>
                <input
                  value={expName}
                  onChange={e => setExpName(e.target.value)}
                  placeholder="e.g. V_Scan_0.8"
                  style={{ width: '100%' }}
                />
              </div>

              {/* Render fields grouped by section */}
              {Object.entries(sectionGroups).map(([section, fields]) => (
                <div key={section} className="eb-section">
                  <div className="eb-section-title">{section}</div>
                  <div className="schema-form">
                    {fields.map(([key, cfg]) => (
                      <React.Fragment key={key}>
                        <label title={cfg.description ?? key}>
                          {key}
                          {cfg.required && <span style={{ color: '#f44747' }}>*</span>}
                        </label>
                        <div>
                          {renderField(key, cfg, form[key] ?? '', v => setField(key, v))}
                        </div>
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              ))}

              <div className="action-row" style={{ marginTop: 12 }}>
                <button className="btn primary" onClick={addToQueue}>
                  {editId !== null ? '✏ Update' : '+ Add to Queue'}
                </button>
                {editId !== null && (
                  <button className="btn" onClick={cancelEdit}>Cancel Edit</button>
                )}
                {editId === null && (
                  <button className="btn" onClick={() => setForm(buildDefaults(fieldConfigs))}>
                    ↺ Reset Defaults
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ─── Right: Queue ───────────────────────────────────────── */}
        <div>
          <div className="panel">
            <div className="section-title-row">
              <span className="section-title" style={{ margin: 0, border: 0 }}>
                Queue ({queue.length})
                {queue.some(e => e.dirty) && <span className="dirty-badge"> ●</span>}
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
                        <td className="q-name">
                          {exp.name}
                          {exp.dirty && <span className="dirty-badge" title="Has unsaved edits"> ●</span>}
                        </td>
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
                          <button className="btn" title="Duplicate" onClick={() => duplicateExp(exp)}>⧉</button>
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

