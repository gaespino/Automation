import { Link } from 'react-router-dom'

const tools = [
  { icon: '📊', title: 'Dashboard', desc: 'Unit tracking hub — failing unit data, experiments, next steps.', href: '/dashboard', accent: '#00d4ff' },
  { icon: '🔧', title: 'THR Tools', desc: '9 engineering analysis tools for GNR, CWF, DMR post-silicon debug.', href: '/thr-tools', accent: '#7000ff' },
]

export default function Home() {
  return (
    <div className="page-container">
      {/* Hero */}
      <div style={{ textAlign: 'center', padding: '3rem 0 2rem' }}>
        <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>⬡</div>
        <h1 style={{
          fontSize: '2.5rem', fontWeight: 800, color: '#00d4ff',
          fontFamily: 'Inter, sans-serif', marginBottom: '0.5rem'
        }}>
          THRHUB
        </h1>
        <p style={{ color: '#a0a0a0', fontSize: '1.05rem', maxWidth: '540px', margin: '0 auto' }}>
          Test Hole Resolution Hub — unified post-silicon engineering platform for
          failing unit root-cause analysis and experiment management.
        </p>
      </div>

      {/* Product tags */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', marginBottom: '3rem' }}>
        {['GNR', 'CWF', 'DMR'].map(p => (
          <span key={p} className="badge badge-info" style={{ fontSize: '0.85rem', padding: '0.3rem 0.9rem' }}>{p}</span>
        ))}
      </div>

      {/* Nav cards */}
      <div className="grid grid-2" style={{ maxWidth: '800px', margin: '0 auto 3rem' }}>
        {tools.map(t => (
          <Link key={t.href} to={t.href} style={{ textDecoration: 'none' }}>
            <div className="card" style={{ borderLeft: `3px solid ${t.accent}`, cursor: 'pointer' }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>{t.icon}</div>
              <h3 style={{ color: t.accent, fontWeight: 700, marginBottom: '0.4rem' }}>{t.title}</h3>
              <p style={{ color: '#a0a0a0', fontSize: '0.88rem', lineHeight: 1.5 }}>{t.desc}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Footer note */}
      <p style={{ textAlign: 'center', color: '#555', fontSize: '0.78rem' }}>
        Flask REST API + React + React Flow — CaaS ready
      </p>
    </div>
  )
}
