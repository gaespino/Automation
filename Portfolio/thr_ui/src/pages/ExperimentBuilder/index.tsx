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
  condition?: { field: string; value: string };
  conditional_options?: { field: string; [key: string]: unknown };
}

type FieldConfigs = Record<string, FieldConfig>;

interface QueuedExperiment {
  id: number;
  name: string;
  fields: Record<string, string>;
  dirty?: boolean;
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

/** Returns true if this field should be shown given the current form values. */
function isFieldVisible(cfg: FieldConfig, form: Record<string, string>): boolean {
  if (!cfg.condition) return true;
  return (form[cfg.condition.field] ?? '') === cfg.condition.value;
}

/** Resolves conditional_options for a field based on the current form values. */
function getEffectiveCfg(cfg: FieldConfig, form: Record<string, string>): FieldConfig {
  if (!cfg.conditional_options) return cfg;
  const { field, ...variants } = cfg.conditional_options as Record<string, unknown>;
  const currentVal = form[field as string] ?? '';
  const variant = (variants as Record<string, unknown>)[currentVal];
  if (!variant || typeof variant !== 'object') return cfg;
  return { ...cfg, ...(variant as Partial<FieldConfig>) };
}

function renderField(
  key: string,
  cfg: FieldConfig,
  value: string,
  onChange: (v: string) => void,
  form?: Record<string, string>,
) {
  const effectiveCfg = form ? getEffectiveCfg(cfg, form) : cfg;
  if (effectiveCfg.options && effectiveCfg.options.length > 0) {
    return (
      <select value={value} onChange={e => onChange(e.target.value)} title={effectiveCfg.description}>
        {effectiveCfg.options.map(opt => <option key={opt}>{opt}</option>)}
      </select>
    );
  }
  if (effectiveCfg.type === 'bool') {
    return (
      <label className="check-label" title={effectiveCfg.description}>
        <input type="checkbox" checked={value === 'true' || value === 'True'}
          onChange={e => onChange(String(e.target.checked))} />
        {key}
      </label>
    );
  }
  if (effectiveCfg.type === 'int' || effectiveCfg.type === 'float') {
    return (
      <input type="number" value={value}
        onChange={e => onChange(e.target.value)}
        title={effectiveCfg.description}
        placeholder={String(effectiveCfg.default ?? '')} />
    );
  }
  return (
    <input value={value}
      onChange={e => onChange(e.target.value)}
      title={effectiveCfg.description}
      placeholder={String(effectiveCfg.default ?? '')} />
  );
}

let nextId = 1;
const TPL_LIST_MIN_ROWS = 2;
const TPL_LIST_MAX_ROWS = 6;

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
  const loadRef      = useRef<HTMLInputElement>(null);
  const tplImportRef = useRef<HTMLInputElement>(null);
  const xlsxImportRef = useRef<HTMLInputElement>(null);

// Templates – persisted to localStorage
  const [templates, setTemplates] = useState<Record<string, Record<string, string>>>(() => {
    try { return JSON.parse(localStorage.getItem('eb_templates') ?? '{}'); }
    catch (err) { console.warn('Failed to load saved templates from localStorage:', err); return {}; }
  });
  const [newTemplateName,  setNewTemplateName]  = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [templatesOpen,    setTemplatesOpen]    = useState(false);

  // Compare / side-by-side view
  const [compareMode,  setCompareMode]  = useState(false);
  const [compareExpId, setCompareExpId] = useState<number | null>(null);

  // Sync templates to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('eb_templates', JSON.stringify(templates));
  }, [templates]);

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

  // ── Queue operations ──────────────────────────────────────────────────────

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
    setQueue(q => [...q, { id: nextId++, name: `${exp.name}_copy`, fields: { ...exp.fields }, dirty: false }]);
  };

  const cancelEdit = () => {
    setEditId(null);
    setExpName('');
    setForm(buildDefaults(fieldConfigs));
    setFormDirty(false);
  };

  const deleteFromQueue = (id: number) => {
    setQueue(q => q.filter(e => e.id !== id));
    if (compareExpId === id) setCompareExpId(null);
    if (editId === id) cancelEdit();
  };

  const clearQueue = () => {
    setQueue([]);
    setEditId(null);
    setCompareExpId(null);
  };

  // ── Template operations ──────────────────────────────────────────────────

  const saveAsTemplate = () => {
    const name = newTemplateName.trim() || expName.trim() || `Template_${Date.now()}`;
    setTemplates(t => ({ ...t, [name]: { ...form } }));
    setNewTemplateName('');
  };

  const applyTemplate = () => {
    if (!selectedTemplate || !templates[selectedTemplate]) return;
    setForm(f => ({ ...f, ...templates[selectedTemplate] }));
    setFormDirty(true);
  };

  const deleteTemplate = () => {
    if (!selectedTemplate) return;
    const name = selectedTemplate;
    setTemplates(t => { const n = { ...t }; delete n[name]; return n; });
    setSelectedTemplate('');
  };

  const exportTemplates = () => {
    const blob = new Blob([JSON.stringify(templates, null, 2)], { type: 'application/json' });
    downloadBlob(blob, 'eb_templates.json');
  };

  const importTemplatesFromFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = ev => {
      try {
        const data = JSON.parse(ev.target?.result as string);
        if (typeof data !== 'object' || Array.isArray(data) || data === null) {
          setError('Templates file must be a JSON object mapping names to field sets.');
          return;
        }
        // Validate each entry: only accept string-keyed objects with scalar values
        const validated: Record<string, Record<string, string>> = {};
        for (const [name, fields] of Object.entries(data)) {
          if (typeof fields === 'object' && fields !== null && !Array.isArray(fields)) {
            validated[name] = Object.fromEntries(
              Object.entries(fields as Record<string, unknown>)
                .filter(([, v]) => v !== null && v !== undefined)
                .map(([k, v]) => [k, String(v)])
            );
          }
        }
        setTemplates(t => ({ ...t, ...validated }));
      } catch { setError('Invalid templates file.'); }
    };
    reader.readAsText(f);
    e.target.value = '';
  };

  const importTemplatesFromExcel = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const formData = new FormData();
    formData.append('file', f);
    try {
      const resp = await fetch(`${BASE}/experiments/templates/import-excel`, {
        method: 'POST',
        body: formData,
      });
      if (!resp.ok) { setError(`${resp.status}: ${await resp.text()}`); return; }
      const data = await resp.json();
      const validated: Record<string, Record<string, string>> = {};
      for (const [name, fields] of Object.entries(data.templates ?? {})) {
        if (typeof fields === 'object' && fields !== null && !Array.isArray(fields)) {
          validated[name] = Object.fromEntries(
            Object.entries(fields as Record<string, unknown>)
              .filter(([, v]) => v !== null && v !== undefined)
              .map(([k, v]) => [k, String(v)])
          );
        }
      }
      setTemplates(t => ({ ...t, ...validated }));
    } catch (err: unknown) {
      setError((err as Error).message);
    }
    e.target.value = '';
  };

  // ── Compare / side-by-side operations ────────────────────────────────────

  const compareExp = (compareMode && compareExpId != null)
    ? queue.find(e => e.id === compareExpId) ?? null
    : null;

  const copyFromCompare = (key: string) => {
    if (!compareExp) return;
    setField(key, compareExp.fields[key] ?? '');
  };

  const copyAllFromCompare = () => {
    if (!compareExp) return;
    setForm(f => ({ ...f, ...compareExp.fields }));
    setFormDirty(true);
  };

  // ── Export / Import .tpl ─────────────────────────────────────────────────

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

        // Normalise an entry to QueuedExperiment regardless of source format.
        // React-saved format:  {id, name, fields: {…}, dirty}
        // PPV-saved format:    {"Test Name": "…", "Content": "…", …}   (flat dict)
        const normalise = (ex: Record<string, unknown>): QueuedExperiment => {
          if (ex.fields && typeof ex.fields === 'object' && !Array.isArray(ex.fields)) {
            // Already React format
            return {
              id: nextId++,
              name: String(ex.name ?? `Experiment_${nextId}`),
              fields: ex.fields as Record<string, string>,
              dirty: false,
            };
          }
          // PPV flat-dict format: use "Test Name" as the experiment name, remaining keys as fields
          const fields: Record<string, string> = {};
          let name = `Experiment_${nextId}`;
          for (const [k, v] of Object.entries(ex)) {
            const str = v === null || v === undefined ? '' : String(v);
            if (k === 'Test Name') name = str || name;
            if (k !== 'Experiment') fields[k] = str;
          }
          return { id: nextId++, name, fields, dirty: false };
        };

        const rawList: unknown[] = Array.isArray(data) ? data : (data.experiments ?? []);
        const reloaded = rawList.map(ex => normalise(ex as Record<string, unknown>));
        setQueue(reloaded);

        // Also restore any templates embedded in a PPV .tpl file
        if (!Array.isArray(data) && data.templates && typeof data.templates === 'object') {
          const validated: Record<string, Record<string, string>> = {};
          for (const [name, fields] of Object.entries(data.templates as Record<string, unknown>)) {
            if (typeof fields === 'object' && fields !== null && !Array.isArray(fields)) {
              validated[name] = Object.fromEntries(
                Object.entries(fields as Record<string, unknown>)
                  .filter(([, v]) => v !== null && v !== undefined)
                  .map(([k, v]) => [k, String(v)])
              );
            }
          }
          if (Object.keys(validated).length) {
            setTemplates(t => ({ ...t, ...validated }));
          }
        }
      } catch { setError('Invalid .tpl file (expected JSON).'); }
    };
    reader.readAsText(f);
    e.target.value = '';
  };

  return (
    <div className="tool-page">
      <h2 className="page-title">🧪 Experiment Builder</h2>

      <div className={`eb-layout${compareMode ? ' eb-compare-mode' : ''}`}>

        {/* ─── Left: Product + Templates + Form ───────────────────── */}
        <div>
          {/* Product selector */}
          <div className="panel">
            <div className="section-title">Product</div>
            <select value={product} onChange={e => setProduct(e.target.value)} style={{ width: '100%' }}>
              {products.map(p => <option key={p}>{p}</option>)}
            </select>
            {loading && <div style={{ color: '#858585', fontSize: 11, marginTop: 6 }}>Loading config…</div>}
          </div>

          {/* Templates panel */}
          <div className="panel" style={{ marginTop: 12 }}>
            <div
              className="section-title-row tpl-header"
              onClick={() => setTemplatesOpen(o => !o)}
            >
              <span className="section-title" style={{ margin: 0, border: 0 }}>
                📁 Templates ({Object.keys(templates).length})
              </span>
              <span style={{ color: '#858585', fontSize: 11 }}>{templatesOpen ? '▲' : '▼'}</span>
            </div>

            {templatesOpen && (
              <div style={{ marginTop: 8 }}>
                <select
                  value={selectedTemplate}
                  onChange={e => setSelectedTemplate(e.target.value)}
                  size={Math.min(Math.max(Object.keys(templates).length, TPL_LIST_MIN_ROWS), TPL_LIST_MAX_ROWS)}
                  className="tpl-list"
                >
                  {Object.keys(templates).sort().map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>

                <div className="form-grid" style={{ margin: '6px 0' }}>
                  <label>Name</label>
                  <input
                    value={newTemplateName}
                    onChange={e => setNewTemplateName(e.target.value)}
                    placeholder={expName || 'Template name'}
                  />
                </div>

                <div className="action-row">
                  <button className="btn primary" onClick={saveAsTemplate}
                    title="Save current form values as a named template">
                    💾 Save
                  </button>
                  <button className="btn" onClick={applyTemplate}
                    disabled={!selectedTemplate}
                    title="Load the selected template into the current form">
                    ↙ Apply
                  </button>
                  <button className="btn danger" onClick={deleteTemplate}
                    disabled={!selectedTemplate}
                    title="Delete the selected template">
                    🗑
                  </button>
                  <button className="btn" onClick={exportTemplates}
                    disabled={!Object.keys(templates).length}
                    title="Export all templates to a JSON file">
                    ⬇
                  </button>
                  <button className="btn" onClick={() => tplImportRef.current?.click()}
                    title="Import templates from a JSON file">
                    📂
                  </button>
                  <button className="btn" onClick={() => xlsxImportRef.current?.click()}
                    title="Import templates from an Excel file (.xlsx, each sheet = one template)">
                    📊
                  </button>
                  <input ref={tplImportRef} type="file" accept=".json"
                    style={{ display: 'none' }} onChange={importTemplatesFromFile} />
                  <input ref={xlsxImportRef} type="file" accept=".xlsx"
                    style={{ display: 'none' }} onChange={importTemplatesFromExcel} />
                </div>
              </div>
            )}
          </div>

          {/* Experiment fields form */}
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

              {Object.entries(sectionGroups).map(([section, fields]) => {
                const visibleFields = fields.filter(([, cfg]) => isFieldVisible(cfg, form));
                if (!visibleFields.length) return null;
                return (
                  <div key={section} className="eb-section">
                    <div className="eb-section-title">{section}</div>
                    <div className="schema-form">
                      {visibleFields.map(([key, cfg]) => (
                        <React.Fragment key={key}>
                          <label title={cfg.description ?? key}>
                            {key}
                            {cfg.required && <span style={{ color: '#f44747' }}>*</span>}
                          </label>
                          <div>
                            {renderField(key, cfg, form[key] ?? '', v => setField(key, v), form)}
                          </div>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                );
              })}

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

        {/* ─── Center: Compare Panel (when active) ────────────────── */}
        {compareMode && (
          <div>
            <div className="panel compare-panel">
              <div className="section-title-row">
                <span className="section-title" style={{ margin: 0, border: 0 }}>
                  ⊞ Compare With
                </span>
                <button className="btn" style={{ fontSize: 10 }}
                  onClick={() => { setCompareMode(false); setCompareExpId(null); }}>
                  ✕ Close
                </button>
              </div>

              <select
                value={compareExpId ?? ''}
                onChange={e => setCompareExpId(e.target.value ? Number(e.target.value) : null)}
                style={{ width: '100%', marginTop: 6, marginBottom: 8 }}
              >
                <option value="">— select experiment —</option>
                {queue.map(exp => (
                  <option key={exp.id} value={exp.id}>{exp.name}</option>
                ))}
              </select>

              {compareExp ? (
                <>
                  <div className="compare-exp-badge">{compareExp.name}</div>
                  <div className="action-row" style={{ marginBottom: 8 }}>
                    <button className="btn primary" onClick={copyAllFromCompare}
                      title="Copy all fields from this experiment into the current form">
                      ← Copy All to Form
                    </button>
                  </div>

                  {Object.entries(sectionGroups).map(([section, fields]) => {
                    const visibleFields = fields.filter(([, cfg]) => isFieldVisible(cfg, form));
                    if (!visibleFields.length) return null;
                    return (
                      <div key={section} className="eb-section">
                        <div className="eb-section-title">{section}</div>
                        <div className="compare-grid">
                          {visibleFields.map(([key]) => {
                            const cmpVal = compareExp.fields[key] ?? '';
                            const curVal = form[key] ?? '';
                            const diff = cmpVal !== curVal;
                            return (
                              <React.Fragment key={key}>
                                <label className={diff ? 'cmp-label-diff' : ''}>
                                  {diff && <span className="cmp-dot" title="Differs from current form">●</span>}
                                  {key}
                                </label>
                                <div className="compare-cell">
                                  <span className={`compare-val${diff ? ' compare-val-diff' : ''}`}>
                                    {cmpVal || '—'}
                                  </span>
                                  {diff && (
                                    <button className="btn cmp-copy-btn" onClick={() => copyFromCompare(key)}
                                      title={`Copy "${cmpVal}" → form`}>
                                      ←
                                    </button>
                                  )}
                                </div>
                              </React.Fragment>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </>
              ) : (
                <div style={{ color: '#858585', fontSize: 12 }}>
                  Select an experiment from the queue to compare its fields with the current form.
                  Differing fields will be highlighted; individual values can be copied to the form.
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─── Right: Queue + Export ──────────────────────────────── */}
        <div>
          <div className="panel">
            <div className="section-title-row">
              <span className="section-title" style={{ margin: 0, border: 0 }}>
                Queue ({queue.length})
                {queue.some(e => e.dirty) && <span className="dirty-badge"> ●</span>}
              </span>
              <div className="action-row">
                <button
                  className={`btn${compareMode ? ' btn-active' : ''}`}
                  onClick={() => setCompareMode(m => !m)}
                  title="Toggle side-by-side compare view"
                >
                  ⊞ {compareMode ? 'Hide Compare' : 'Compare'}
                </button>
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
                      <tr key={exp.id}
                        className={[
                          editId === exp.id ? 'row-editing' : '',
                          compareExpId === exp.id ? 'row-comparing' : '',
                        ].filter(Boolean).join(' ')}
                      >
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
                          {compareMode && (
                            <button
                              className={`btn${compareExpId === exp.id ? ' btn-active' : ''}`}
                              title="Compare with this experiment"
                              onClick={() => setCompareExpId(id => id === exp.id ? null : exp.id)}
                            >⊞</button>
                          )}
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

