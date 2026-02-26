import { useState, useEffect } from 'react'
import { dashboardApi } from '../services/api'

function StatCard({ label, value, sub, accent = '#00d4ff' }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color: accent }}>{value ?? '—'}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}

function StatusBadge({ status }) {
  const map = {
    fail: 'badge-danger', failing: 'badge-danger', reject: 'badge-danger',
    pass: 'badge-success', active: 'badge-info', unknown: 'badge-muted',
  }
  return <span className={`badge ${map[status?.toLowerCase()] ?? 'badge-muted'}`}>{status}</span>
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [units, setUnits] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({ product: '', status: '' })
  const [toast, setToast] = useState(null)

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const loadData = async () => {
    try {
      const [s, u] = await Promise.all([
        dashboardApi.getStats(),
        dashboardApi.getUnits(
          Object.fromEntries(Object.entries(filter).filter(([, v]) => v))
        ),
      ])
      setStats(s)
      setUnits(u)
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [filter])  // eslint-disable-line

  const PRODUCTS = ['', 'GNR', 'CWF', 'DMR']
  const STATUSES = ['', 'active', 'fail', 'pass', 'unknown']

  return (
    <div className="page-container">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Unit tracking hub — experiments, rejects, and next steps</p>
        </div>
        <button className="btn btn-outline btn-sm" onClick={loadData}>↻ Refresh</button>
      </div>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-3 mb-4" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(180px,1fr))' }}>
          <StatCard label="Total Units"   value={stats.total_units}   accent="#00d4ff" />
          <StatCard label="Failing Units" value={stats.failing_count} accent="#ff4d4d"
            sub={stats.failing_count > 0 ? 'requires attention' : 'all clear'} />
          {Object.entries(stats.by_product || {}).map(([prod, cnt]) => (
            <StatCard key={prod} label={prod} value={cnt} accent="#7000ff" sub="units" />
          ))}
        </div>
      )}

      {/* Failing units alert */}
      {stats?.failing_count > 0 && (
        <div className="card mb-4" style={{ borderLeft: '3px solid #ff4d4d' }}>
          <div className="flex items-center gap-2 mb-2">
            <span style={{ color: '#ff4d4d', fontWeight: 700 }}>⚠ Failing Units</span>
            <span className="badge badge-danger">{stats.failing_count}</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ color: '#a0a0a0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                {['VID','Product','Status','Bucket','Fail Reason','Updated'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '0.3rem 0.6rem', fontWeight: 500 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {stats.failing_units.map(u => (
                <tr key={u.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '0.35rem 0.6rem', color: '#e0e0e0', fontFamily: 'var(--font-mono)' }}>{u.vid || u.id}</td>
                  <td style={{ padding: '0.35rem 0.6rem' }}><span className="badge badge-info">{u.product}</span></td>
                  <td style={{ padding: '0.35rem 0.6rem' }}><StatusBadge status={u.status} /></td>
                  <td style={{ padding: '0.35rem 0.6rem', color: '#a0a0a0' }}>{u.bucket || '—'}</td>
                  <td style={{ padding: '0.35rem 0.6rem', color: '#ff4d4d', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>{u.fail_reason || '—'}</td>
                  <td style={{ padding: '0.35rem 0.6rem', color: '#555', fontSize: '0.75rem' }}>{u.updated_at?.slice(0,19) || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 mb-4" style={{ flexWrap: 'wrap' }}>
        <div style={{ flex: '0 0 180px' }}>
          <label>Filter by Product</label>
          <select value={filter.product} onChange={e => setFilter(f => ({ ...f, product: e.target.value }))}>
            {PRODUCTS.map(p => <option key={p} value={p}>{p || 'All Products'}</option>)}
          </select>
        </div>
        <div style={{ flex: '0 0 180px' }}>
          <label>Filter by Status</label>
          <select value={filter.status} onChange={e => setFilter(f => ({ ...f, status: e.target.value }))}>
            {STATUSES.map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
          </select>
        </div>
      </div>

      {/* Units table */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 style={{ color: '#00d4ff', fontWeight: 600 }}>Units ({units.length})</h3>
          <AddUnitButton onCreated={loadData} showToast={showToast} />
        </div>

        {loading ? (
          <p className="text-muted">Loading...</p>
        ) : units.length === 0 ? (
          <p className="text-muted" style={{ textAlign: 'center', padding: '2rem' }}>
            No units found. Create a unit to get started.
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.83rem' }}>
              <thead>
                <tr style={{ color: '#a0a0a0', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                  {['VID','Product','Bucket','Status','Experiments','Updated'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '0.45rem 0.75rem', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {units.map(u => (
                  <tr key={u.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', transition: 'background 0.1s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(0,212,255,0.03)'}
                    onMouseLeave={e => e.currentTarget.style.background = ''}
                  >
                    <td style={{ padding: '0.45rem 0.75rem', color: '#e0e0e0', fontFamily: 'var(--font-mono)' }}>{u.vid || u.id}</td>
                    <td style={{ padding: '0.45rem 0.75rem' }}><span className="badge badge-info">{u.product}</span></td>
                    <td style={{ padding: '0.45rem 0.75rem', color: '#a0a0a0' }}>{u.bucket || '—'}</td>
                    <td style={{ padding: '0.45rem 0.75rem' }}><StatusBadge status={u.status} /></td>
                    <td style={{ padding: '0.45rem 0.75rem', color: '#a0a0a0' }}>{(u.experiments || []).length}</td>
                    <td style={{ padding: '0.45rem 0.75rem', color: '#555', fontSize: '0.75rem' }}>{u.updated_at?.slice(0,19) || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function AddUnitButton({ onCreated, showToast }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ vid: '', product: 'GNR', bucket: '', status: 'active' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await dashboardApi.createUnit(form)
      showToast('Unit created.', 'success')
      setOpen(false)
      setForm({ vid: '', product: 'GNR', bucket: '', status: 'active' })
      onCreated()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  return (
    <>
      <button className="btn btn-outline btn-sm" onClick={() => setOpen(true)}>+ Add Unit</button>
      {open && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 3000
        }}>
          <div className="card" style={{ width: 420, position: 'relative' }}>
            <h4 style={{ color: '#00d4ff', marginBottom: '1rem' }}>Add Unit</h4>
            <form onSubmit={handleSubmit}>
              <label>Visual ID (VID) *</label>
              <input value={form.vid} onChange={e => setForm(f => ({ ...f, vid: e.target.value }))}
                placeholder="e.g. A1B2C3" required className="mb-2" />
              <label>Product</label>
              <select value={form.product} onChange={e => setForm(f => ({ ...f, product: e.target.value }))} className="mb-2">
                {['GNR','CWF','DMR'].map(p => <option key={p}>{p}</option>)}
              </select>
              <label>Bucket</label>
              <input value={form.bucket} onChange={e => setForm(f => ({ ...f, bucket: e.target.value }))}
                placeholder="e.g. 3STRIKE" className="mb-2" />
              <label>Status</label>
              <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))} className="mb-4">
                {['active','fail','pass','unknown'].map(s => <option key={s}>{s}</option>)}
              </select>
              <div className="flex gap-2">
                <button type="submit" className="btn btn-primary w-full">Create</button>
                <button type="button" className="btn btn-outline" onClick={() => setOpen(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
