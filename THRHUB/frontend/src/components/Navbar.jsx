import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'

const TOOLS = [
  { name: 'PTC Loop Parser',          href: '/thr-tools/loop-parser' },
  { name: 'PPV MCA Report',           href: '/thr-tools/mca-report' },
  { name: 'MCA Single Decoder',       href: '/thr-tools/mca-decoder' },
  { name: 'DPMB Requests',            href: '/thr-tools/dpmb' },
  { name: 'File Handler',             href: '/thr-tools/file-handler' },
  { name: 'Framework Report Builder', href: '/thr-tools/framework-report' },
  { name: 'Automation Flow Designer', href: '/thr-tools/automation-designer' },
  { name: 'Experiment Builder',       href: '/thr-tools/experiment-builder' },
  { name: 'Fuse File Generator',      href: '/thr-tools/fuse-generator' },
]

const navStyle = {
  display: 'flex',
  alignItems: 'center',
  padding: '0 1.5rem',
  height: '54px',
  background: '#15171e',
  borderBottom: '1px solid rgba(255,255,255,0.08)',
  fontFamily: 'Inter, sans-serif',
  position: 'sticky',
  top: 0,
  zIndex: 1000,
  gap: '1.5rem',
}

const linkStyle = (active) => ({
  color: active ? '#00d4ff' : '#a0a0a0',
  textDecoration: 'none',
  fontSize: '0.88rem',
  fontWeight: active ? 600 : 400,
  padding: '0.3rem 0',
  borderBottom: active ? '2px solid #00d4ff' : '2px solid transparent',
  transition: 'color 0.15s',
})

const dropdownMenuStyle = {
  position: 'absolute',
  top: '100%',
  left: 0,
  background: '#1a1d26',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '8px',
  padding: '0.4rem 0',
  minWidth: '220px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
  zIndex: 2000,
}

export default function Navbar() {
  const [toolsOpen, setToolsOpen] = useState(false)

  return (
    <nav style={navStyle}>
      {/* Brand */}
      <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ color: '#00d4ff', fontSize: '1.1rem', lineHeight: 1 }}>●</span>
        <span style={{ color: '#e0e0e0', fontWeight: 700, fontSize: '1rem' }}>THRHUB</span>
      </Link>

      {/* Nav links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.2rem', marginLeft: 'auto' }}>
        <NavLink to="/dashboard" style={({ isActive }) => linkStyle(isActive)}>
          Dashboard
        </NavLink>

        {/* THR Tools dropdown */}
        <div style={{ position: 'relative' }}
          onMouseEnter={() => setToolsOpen(true)}
          onMouseLeave={() => setToolsOpen(false)}
        >
          <NavLink
            to="/thr-tools"
            style={({ isActive }) => linkStyle(isActive)}
            onClick={() => setToolsOpen(false)}
          >
            THR Tools ▾
          </NavLink>
          {toolsOpen && (
            <div style={dropdownMenuStyle}>
              {TOOLS.map(t => (
                <NavLink
                  key={t.href}
                  to={t.href}
                  style={({ isActive }) => ({
                    display: 'block',
                    padding: '0.45rem 1rem',
                    fontSize: '0.83rem',
                    textDecoration: 'none',
                    color: isActive ? '#00d4ff' : '#a0a0a0',
                    background: isActive ? 'rgba(0,212,255,0.07)' : 'transparent',
                    transition: 'background 0.1s, color 0.1s',
                  })}
                  onClick={() => setToolsOpen(false)}
                >
                  {t.name}
                </NavLink>
              ))}
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
