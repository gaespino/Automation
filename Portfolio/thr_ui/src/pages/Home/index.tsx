import React from 'react';
import { Link } from 'react-router-dom';
import './style.css';

const TOOLS = [
  { path: '/mca-report',   label: '📋 MCA Report',           desc: 'Generate MCA analysis reports' },
  { path: '/mca-decoder',  label: '🔍 MCA Decoder',           desc: 'Decode MCA register values' },
  { path: '/loop-parser',  label: '🔄 Loop Parser',           desc: 'Parse loop log files' },
  { path: '/file-handler', label: '📁 File Handler',          desc: 'Merge and append Excel files' },
  { path: '/framework',    label: '📊 Framework Report',      desc: 'Generate framework reports' },
  { path: '/automation',   label: '⚙️ Automation Designer',   desc: 'Visual automation flow designer' },
  { path: '/experiment',   label: '🧪 Experiment Builder',    desc: 'Build experiment templates' },
  { path: '/fuses',        label: '🔌 Fuse Generator',        desc: 'Generate fuse config files' },
];

export default function Home() {
  return (
    <div className="home-page">
      <div className="home-hero">
        <h1 className="home-title">◆ THR Tools</h1>
        <p className="home-subtitle">Thermal &amp; Hardware Reliability Toolset</p>
      </div>

      <div className="home-cards">
        <a className="home-card dashboard-card" href="/dashboard/" target="_blank" rel="noreferrer">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-title">Dashboard</div>
            <div className="card-desc">View THR metrics, charts and live results</div>
          </div>
          <span className="card-ext">↗</span>
        </a>

        <div className="home-card">
          <div className="card-icon">🔧</div>
          <div className="card-content">
            <div className="card-title">THR Tools</div>
            <div className="tools-grid">
              {TOOLS.map(t => (
                <Link key={t.path} to={t.path} className="tool-link">
                  <span className="tool-link-name">{t.label}</span>
                  <span className="tool-link-desc">{t.desc}</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
