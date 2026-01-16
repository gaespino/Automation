# THR Debug Tools - Quick Start Guide

**Version:** 2.0
**Release Date:** January 15, 2026
**Organization:** Intel Corporation - Test & Validation
**Classification:** Intel Confidential
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)
**Repository:** `c:\Git\Automation\PPV\`
**Documentation:** `c:\Git\Automation\S2T\DOCUMENTATION\`

---

## Overview

The **THR Debug Tools** (Test Hole Resolution Debug Tools) suite is a comprehensive Python GUI application for unit characterization, post-silicon validation, and debug workflows. This tool hub integrates 8 specialized tools for MCA analysis, experiment configuration, data collection automation, and comprehensive report generation.

**Main Entry Point:** `run.py`

---

## 🚀 Quick Start

### Launch the Tools Hub
```bash
cd c:\Git\Automation\PPV
python run.py
```

The application will:
1. Display the THR Debug Tools banner
2. Prompt for product selection (GNR/CWF/DMR)
3. Launch the main Tools Hub with all 8 tools

---

## 📚 Complete Documentation

All comprehensive documentation is located in the centralized documentation folder:

**Location:** `c:\Git\Automation\S2T\DOCUMENTATION\`

### Available Documentation

1. **[THR_DEBUG_TOOLS_USER_MANUAL.md](THR_DEBUG_TOOLS_USER_MANUAL.md)**
   - Complete user manual for all 8 tools
   - GUI and programmatic usage instructions
   - Parameter references and examples
   - Integration workflows
   - Troubleshooting guide
   - Advanced topics

2. **[THR_DEBUG_TOOLS_FLOWS.md](THR_DEBUG_TOOLS_FLOWS.md)**
   - Complete debug workflow documentation
   - Tool integration matrix and data flows
   - Step-by-step workflow examples
   - Best practices and patterns
   - Flow templates

3. **[THR_DebugTools_Examples.ipynb](THR_DebugTools_Examples.ipynb)**
   - Interactive Jupyter notebook
   - Executable examples for launching tools
   - GUI and programmatic usage patterns
   - End-to-end workflow examples

4. **[../README.md](THR_DOCUMENTATION_README.md)**
   - Navigation guide for all S2T documentation
   - Quick reference for finding specific topics

---

## 🛠️ Tools Overview

### 1. PTC Loop Parser
**Purpose:** Parse PTC loop data from Framework execution folders
**Color:** Blue (#3498db)
**Module:** `gui/PPVLoopChecks.py`

### 2. PPV MCA Report Builder
**Purpose:** Generate comprehensive MCA reports from multiple data sources
**Color:** Red (#e74c3c)
**Module:** `gui/PPVDataChecks.py`

### 3. DPMB Bucketer Requests
**Purpose:** Query Intel's DPMB API for historical bucket data
**Color:** Purple (#9b59b6)
**Module:** `api/dpmb.py`

### 4. File Handler
**Purpose:** Merge or append Excel report files
**Color:** Orange (#f39c12)
**Module:** `gui/PPVFileHandler.py`

### 5. Framework Report Builder
**Purpose:** Generate comprehensive Framework execution reports
**Color:** Turquoise (#1abc9c)
**Module:** `gui/PPVFrameworkReport.py`

### 6. Automation Flow Designer
**Purpose:** Visual flow designer for test automation
**Color:** Teal (#1abc9c)
**Module:** `gui/AutomationDesigner.py`

### 7. Experiment Builder
**Purpose:** Excel-like interface for Control Panel configurations
**Color:** Teal (#1abc9c)
**Module:** `gui/ExperimentBuilder.py`

### 8. MCA Single Line Decoder
**Purpose:** Interactive decoder for MCA register values
**Color:** Red (#e74c3c)
**Module:** `gui/MCADecoder.py`

---

## 📂 PPV Folder Structure

```
PPV/
├── run.py                    # Main entry point - Launch Tools Hub
├── gui/                      # GUI modules for all tools
│   ├── PPVTools.py          # Main Tools Hub
│   ├── PPVLoopChecks.py     # PTC Loop Parser
│   ├── PPVDataChecks.py     # MCA Report Builder
│   ├── PPVFileHandler.py    # File Handler
│   ├── PPVFrameworkReport.py # Framework Report Builder
│   ├── AutomationDesigner.py # Automation Flow Designer
│   ├── ExperimentBuilder.py  # Experiment Builder
│   ├── MCADecoder.py        # MCA Decoder
│   └── ProductSelector.py   # Product selection dialog
├── parsers/                  # Data parsing modules
│   ├── MCAparser.py         # MCA parsing engine
│   ├── PPVLoopsParser.py    # Loop data parser
│   ├── Frameworkparser.py   # Framework log parser
│   └── FrameworkAnalyzer.py # Experiment analysis
├── Decoder/                  # MCA decoders
│   ├── decoder.py           # Main decoder engine
│   ├── GNR_decoders.py      # GNR-specific decoders
│   ├── CWF_decoders.py      # CWF-specific decoders
│   └── DMR_decoders.py      # DMR-specific decoders
├── api/                      # API modules
│   └── dpmb.py              # DPMB API client
├── utils/                    # Utility modules
│   ├── PPVReportMerger.py   # Report merge/append
│   └── ExcelReports.py      # Excel generation
└── configs/                  # Configuration templates
    ├── GNRControlPanelConfig.json
    ├── CWFControlPanelConfig.json
    └── DMRControlPanelConfig.json
```

---

## 💡 Usage Modes

### Mode 1: Tools Hub Interface (Primary)
Launch the main hub and access all tools from a unified interface:
```bash
cd c:\Git\Automation\PPV
python run.py
```

### Mode 2: Individual Tool Launch (Advanced)
Launch specific tools directly as standalone windows:
```python
import sys
sys.path.insert(0, r'c:\Git\Automation\PPV')

# Launch specific tool
from gui.PPVDataChecks import PPVReportGUI
import tkinter as tk
root = tk.Tk()
PPVReportGUI(root, default_product="GNR")
root.mainloop()
```

### Mode 3: Programmatic API (Integration)
Use parsers and APIs programmatically for automation:
```python
from PPV.parsers.MCAparser import ppv_report
ppv_report(mode='Bucketer', product='GNR', ...)
```

---

## 🎯 Common Workflows

### Workflow 1: Offline Characterization
1. Launch Tools Hub → **DPMB Bucketer Requests**
2. Query historical data for unit
3. Launch **PPV MCA Report Builder**
4. Generate MCA analysis
5. Launch **MCA Decoder** for deep dive
6. Launch **Experiment Builder** to create tests

### Workflow 2: Post-Execution Analysis
1. Launch Tools Hub → **Framework Report Builder**
2. Select Visual ID and configure experiments
3. Generate comprehensive report
4. Launch **File Handler** to consolidate multiple runs

### Workflow 3: Loop Characterization
1. Launch Tools Hub → **Experiment Builder**
2. Configure loop experiments
3. Execute on Control Panel (external)
4. Launch **PTC Loop Parser**
5. Launch **Framework Report Builder**
6. Use **File Handler** to merge weekly reports

### Workflow 4: Automation Design
1. Launch Tools Hub → **Experiment Builder**
2. Create experiment library
3. Launch **Automation Flow Designer**
4. Design flow with visual canvas
5. Export to Control Panel

---

## 📖 Documentation Quick Reference

| I want to... | See this documentation |
|-------------|----------------------|
| Understand all tools | [THR_DEBUG_TOOLS_USER_MANUAL.md](THR_DEBUG_TOOLS_USER_MANUAL.md) |
| Learn complete workflows | [THR_DEBUG_TOOLS_FLOWS.md](THR_DEBUG_TOOLS_FLOWS.md) |
| See executable examples | [THR_DebugTools_Examples.ipynb](THR_DebugTools_Examples.ipynb) |
| Launch Tools Hub | Run `python run.py` in PPV folder |
| Query DPMB data | User Manual - Tool 3 |
| Generate MCA reports | User Manual - Tool 2 |
| Parse loop data | User Manual - Tool 1 |
| Build Framework reports | User Manual - Tool 5 |
| Decode MCA registers | User Manual - Tool 8 |
| Merge reports | User Manual - Tool 4 |
| Design automation flows | User Manual - Tool 6 |
| Create experiments | User Manual - Tool 7 |
| Understand tool integration | [THR_DEBUG_TOOLS_FLOWS.md](THR_DEBUG_TOOLS_FLOWS.md) - Tool Integration Matrix |
| See workflow examples | [THR_DEBUG_TOOLS_FLOWS.md](THR_DEBUG_TOOLS_FLOWS.md) - Workflow Examples |

---

## 🔧 Requirements

### Python Dependencies
```bash
pip install pandas openpyxl tabulate requests tkinter
```

### System Requirements
- Python 3.7+
- Windows OS (for GUI components)
- Network access to Framework server (for Framework Report Builder)
- Intel network access (for DPMB API)

---

## 📧 Support

**Maintainer:** Gabriel Espinoza
**Email:** gabriel.espinoza.ballestero@intel.com
**Organization:** Intel Corporation - Test & Validation
**Version:** 2.0
**Release Date:** January 15, 2026

**For Technical Support:**
- Questions or issues: Contact maintainer via email
- Bug reports: Include version, product selection, and error logs
- Feature requests: Provide detailed use case description

**Documentation Resources:**
- Complete User Manual: [THR_DEBUG_TOOLS_USER_MANUAL.md](THR_DEBUG_TOOLS_USER_MANUAL.md)
- Workflow Guides: [THR_DEBUG_TOOLS_FLOWS.md](THR_DEBUG_TOOLS_FLOWS.md)
- Examples: [THR_DEBUG_TOOLS_EXAMPLES.ipynb](THR_DEBUG_TOOLS_EXAMPLES.ipynb)
- All documentation: `c:\Git\Automation\S2T\DOCUMENTATION\`

---

**© 2026 Intel Corporation. Intel Confidential.**

## 🔗 Related Documentation

- **BASELINE Framework Documentation:** See [../README.md](THR_DOCUMENTATION_README.md) for SystemDebug, ControlPanel, AutomationPanel
- **S2T Module Documentation:** See [../README.md](THR_DOCUMENTATION_README.md) for dpmChecks, SetTesterRegs
- **Main Documentation Index:** [../README.md](THR_DOCUMENTATION_README.md)
