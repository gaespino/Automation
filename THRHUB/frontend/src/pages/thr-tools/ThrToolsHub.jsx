import { Link } from 'react-router-dom'

const TOOLS = [
  {
    title: 'PTC Loop Parser',
    desc: 'Parse logs from PTC experiment data and generate DPMB report format files.',
    features: ['Automated log parsing', 'DPMB format output', 'Batch processing support'],
    accent: '#00d4ff',
    icon: '📄',
    href: '/thr-tools/loop-parser',
  },
  {
    title: 'PPV MCA Report',
    desc: 'Generate comprehensive MCA reports from Bucketer files or S2T Logger data.',
    features: ['Bucketer file analysis', 'S2T Logger integration', 'MCA decoding & visualization'],
    accent: '#ff4d4d',
    icon: '📊',
    href: '/thr-tools/mca-report',
  },
  {
    title: 'MCA Single Decoder',
    desc: 'Decode individual MCA registers for CHA, LLC, CORE, MEMORY, IO, and First Error.',
    features: ['Single register decode', 'Multi-product support', 'GNR / CWF / DMR compatible'],
    accent: '#ff6b8a',
    icon: '🔍',
    href: '/thr-tools/mca-decoder',
  },
  {
    title: 'DPMB Requests',
    desc: 'Interface for Bucketer data requests through DPMB API.',
    features: ['Direct API connection', 'Automated data retrieval', 'Custom query builder'],
    accent: '#7000ff',
    icon: '🔗',
    href: '/thr-tools/dpmb',
  },
  {
    title: 'File Handler',
    desc: 'Merge and manage multiple data files efficiently.',
    features: ['Merge DPMB format files', 'Append MCA reports', 'Batch file operations'],
    accent: '#ffbd2e',
    icon: '📁',
    href: '/thr-tools/file-handler',
  },
  {
    title: 'Framework Report Builder',
    desc: 'Create comprehensive reports from Debug Framework experiment data.',
    features: ['Unit overview generation', 'Summary file merging', 'Multi-experiment analysis'],
    accent: '#00ff9d',
    icon: '📋',
    href: '/thr-tools/framework-report',
  },
  {
    title: 'Automation Flow Designer',
    desc: 'Visual engineering diagramming tool — design automation test flows with drag-and-drop nodes.',
    features: ['React Flow canvas', 'Node-based flow design', 'Export to JSON / import'],
    accent: '#00c9a7',
    icon: '⬡',
    href: '/thr-tools/automation-designer',
  },
  {
    title: 'Experiment Builder',
    desc: 'Excel-notebook-style tool for building multi-experiment JSON configs for Debug Framework.',
    features: ['Tab-per-experiment interface', 'Per-product field config', 'Import/Export JSON'],
    accent: '#36d7b7',
    icon: '🧪',
    href: '/thr-tools/experiment-builder',
  },
]

const FULL_WIDTH = {
  title: 'Fuse File Generator',
  desc: 'Engineering tool for managing and generating fuse configuration files from CSV data.',
  features: ['Parse and filter fuse CSV files', 'Product-specific IP configuration', 'Generate .fuse files for fusefilegen'],
  accent: '#ff9f45',
  icon: '⚡',
  href: '/thr-tools/fuse-generator',
}

function ToolCard({ tool, fullWidth = false }) {
  return (
    <div style={{ gridColumn: fullWidth ? '1 / -1' : undefined }}>
      <Link to={tool.href} style={{ textDecoration: 'none' }}>
        <div className="card h-full" style={{ borderLeft: `3px solid ${tool.accent}`, cursor: 'pointer', height: '100%' }}>
          <div className="flex items-center gap-2 mb-2">
            <span style={{ fontSize: '1.3rem' }}>{tool.icon}</span>
            <span style={{ color: tool.accent, fontWeight: 700, fontSize: '0.95rem' }}>{tool.title}</span>
          </div>
          <p style={{ color: '#e0e0e0', fontSize: '0.85rem', marginBottom: '0.75rem', lineHeight: 1.5 }}>{tool.desc}</p>
          <ul style={{ paddingLeft: '1.2rem', margin: 0, lineHeight: 1.8 }}>
            {tool.features.map(f => (
              <li key={f} style={{ color: '#a0a0a0', fontSize: '0.8rem' }}>{f}</li>
            ))}
          </ul>
          <div style={{ marginTop: '1rem' }}>
            <span style={{
              color: tool.accent, fontSize: '0.8rem', fontWeight: 600,
              border: `1px solid ${tool.accent}`, padding: '0.25rem 0.7rem',
              borderRadius: '4px', display: 'inline-block'
            }}>
              Open Tool →
            </span>
          </div>
        </div>
      </Link>
    </div>
  )
}

export default function ThrToolsHub() {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">THR Tools</h1>
        <p className="page-subtitle">Debug &amp; analysis tools for GNR, CWF, and DMR products.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        {TOOLS.map(t => <ToolCard key={t.href} tool={t} />)}
        <ToolCard tool={FULL_WIDTH} fullWidth />
      </div>
    </div>
  )
}
