import React from 'react';
import { NavLink } from 'react-router-dom';
import './Navbar.css';

const TOOLS = [
  { path: '/mca-report',      label: 'MCA Report' },
  { path: '/mca-decoder',     label: 'MCA Decoder' },
  { path: '/loop-parser',     label: 'Loop Parser' },
  { path: '/file-handler',    label: 'File Handler' },
  { path: '/framework',       label: 'Framework Report' },
  { path: '/automation',      label: 'Automation Designer' },
  { path: '/experiment',      label: 'Experiment Builder' },
  { path: '/fuses',           label: 'Fuse Generator' },
];

export default function Navbar() {
  return (
    <nav className="navbar">
      <a className="navbar-brand" href="/">◆ THR Tools</a>
      <div className="navbar-links">
        {TOOLS.map(t => (
          <NavLink
            key={t.path}
            to={t.path}
            className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
          >
            {t.label}
          </NavLink>
        ))}
        <a className="nav-item ext" href="/dashboard/" target="_blank" rel="noreferrer">
          Dashboard ↗
        </a>
      </div>
    </nav>
  );
}
