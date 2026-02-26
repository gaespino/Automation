import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import './Navbar.css';

const TOOLS = [
  { path: '/mca-report',   label: '📋 MCA Report' },
  { path: '/mca-decoder',  label: '🔍 MCA Decoder' },
  { path: '/loop-parser',  label: '🔄 Loop Parser' },
  { path: '/file-handler', label: '📁 File Handler' },
  { path: '/framework',    label: '📊 Framework Report' },
  { path: '/automation',   label: '⚙️ Automation Designer' },
  { path: '/experiment',   label: '🧪 Experiment Builder' },
  { path: '/fuses',        label: '🔌 Fuse Generator' },
  { path: '/dpmb',         label: '📡 DPMB Requests' },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="navbar">
      <a className="navbar-brand" href="/thr/">◆ THR Tools</a>

      <div
        className={`nav-dropdown${open ? ' open' : ''}`}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
      >
        <button className="nav-dropdown-btn">
          Tools ▾
        </button>
        <div className="nav-dropdown-menu">
          {TOOLS.map(t => (
            <NavLink
              key={t.path}
              to={t.path}
              className={({ isActive }) => 'nav-dropdown-item' + (isActive ? ' active' : '')}
              onClick={() => setOpen(false)}
            >
              {t.label}
            </NavLink>
          ))}
        </div>
      </div>

      <div className="navbar-right">
        <NavLink
          to="/"
          end
          className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
        >
          ⊞ Home
        </NavLink>
        <a className="nav-item dashboard-link" href="/dashboard/">
          📊 Dashboard
        </a>
      </div>
    </nav>
  );
}
