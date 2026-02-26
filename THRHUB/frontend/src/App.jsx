import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import ThrToolsHub from './pages/thr-tools/ThrToolsHub'
import AutomationDesigner from './pages/thr-tools/AutomationDesigner'
import ExperimentBuilder from './pages/thr-tools/ExperimentBuilder'
import MCADecoder from './pages/thr-tools/MCADecoder'
import MCAReport from './pages/thr-tools/MCAReport'
import LoopParser from './pages/thr-tools/LoopParser'
import DPMB from './pages/thr-tools/DPMB'
import FileHandler from './pages/thr-tools/FileHandler'
import FrameworkReport from './pages/thr-tools/FrameworkReport'
import FuseGenerator from './pages/thr-tools/FuseGenerator'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="thr-tools" element={<ThrToolsHub />} />
          <Route path="thr-tools/automation-designer" element={<AutomationDesigner />} />
          <Route path="thr-tools/experiment-builder" element={<ExperimentBuilder />} />
          <Route path="thr-tools/mca-decoder" element={<MCADecoder />} />
          <Route path="thr-tools/mca-report" element={<MCAReport />} />
          <Route path="thr-tools/loop-parser" element={<LoopParser />} />
          <Route path="thr-tools/dpmb" element={<DPMB />} />
          <Route path="thr-tools/file-handler" element={<FileHandler />} />
          <Route path="thr-tools/framework-report" element={<FrameworkReport />} />
          <Route path="thr-tools/fuse-generator" element={<FuseGenerator />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
