import React from 'react';
import { Link } from 'react-router-dom';
import './style.css';

const TOOLS = [
  { path: '/mca-report',   icon: '📋', label: 'MCA Report',           desc: 'Generate MCA analysis reports from Bucketer or S2T Logger files' },
  { path: '/mca-decoder',  icon: '🔍', label: 'MCA Decoder',           desc: 'Decode MCA register values for CHA, Core, Memory and IO banks' },
  { path: '/loop-parser',  icon: '🔄', label: 'PTC Loop Parser',       desc: 'Parse and process PTC loop log files' },
  { path: '/file-handler', icon: '📁', label: 'File Handler',          desc: 'Merge and append Excel files and tables' },
  { path: '/framework',    icon: '📊', label: 'Framework Report',      desc: 'Generate framework reports from experiment folder trees' },
  { path: '/automation',   icon: '⚙️', label: 'Automation Designer',   desc: 'Visual flow designer for PPV automation sequences' },
  { path: '/experiment',   icon: '🧪', label: 'Experiment Builder',    desc: 'Build and save experiment configuration templates' },
  { path: '/fuses',        icon: '🔌', label: 'Fuse Generator',        desc: 'Search, select and generate product fuse config files' },
  { path: '/dpmb',         icon: '📡', label: 'DPMB Requests',         desc: 'Submit and track DPMB bucketer job requests' },
];

export default function Home() {
  return (
    <div className="home-page">
      <div className="home-hero">
        <h1 className="home-title">◆ THR Tools</h1>
        <p className="home-subtitle">Thermal &amp; Hardware Reliability Toolset — GNR · CWF · DMR</p>
      </div>

      {/* Dashboard section — top, prominent, full-width */}
      <a className="home-dashboard-section" href="/dashboard/">
        <div className="home-dashboard-inner">
          <span className="home-dashboard-icon">📊</span>
          <div className="home-dashboard-text">
            <span className="home-dashboard-title">Unit Portfolio Dashboard</span>
            <span className="home-dashboard-desc">View THR metrics, experiment results, charts and live unit data</span>
          </div>
          <span className="home-dashboard-arrow">Open Dashboard →</span>
        </div>
      </a>

      {/* THR Tools section — labelled enclosure */}
      <div className="home-tools-section">
        <div className="home-tools-header">
          <span className="home-tools-header-icon">🔧</span>
          <span className="home-tools-header-label">THR Tools</span>
          <span className="home-tools-header-sub">Select a tool to get started</span>
        </div>
        <div className="tools-grid">
          {TOOLS.map(t => (
            <Link key={t.path} to={t.path} className="tool-tile">
              <span className="tool-tile-icon">{t.icon}</span>
              <span className="tool-tile-name">{t.label}</span>
              <span className="tool-tile-desc">{t.desc}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
