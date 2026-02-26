import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import './theme.css';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import AutomationDesigner from './pages/AutomationDesigner';
import MCAReport from './pages/MCAReport';
import MCADecoder from './pages/MCADecoder';
import LoopParser from './pages/LoopParser';
import FileHandler from './pages/FileHandler';
import FrameworkReport from './pages/FrameworkReport';
import FuseGenerator from './pages/FuseGenerator';
import ExperimentBuilder from './pages/ExperimentBuilder';
import DPMBRequests from './pages/DPMBRequests';

export default function App() {
  return (
    <BrowserRouter basename="/thr">
      <Toaster />
      <Navbar />
      <Routes>
        <Route path="/"             element={<Home />} />
        <Route path="/automation"   element={<AutomationDesigner />} />
        <Route path="/mca-report"   element={<MCAReport />} />
        <Route path="/mca-decoder"  element={<MCADecoder />} />
        <Route path="/loop-parser"  element={<LoopParser />} />
        <Route path="/file-handler" element={<FileHandler />} />
        <Route path="/framework"    element={<FrameworkReport />} />
        <Route path="/fuses"        element={<FuseGenerator />} />
        <Route path="/experiment"   element={<ExperimentBuilder />} />
        <Route path="/dpmb"         element={<DPMBRequests />} />
        <Route path="*"             element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
