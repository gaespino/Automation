# Debug Framework & S2T Documentation - README

**Version:** 1.7
**Release Date:** February 16, 2026
**Organization:** Intel Corporation - Test & Validation
**Classification:** Intel Confidential
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

---

## � NEW USER QUICK START

**First time installing?** Use the automated GUI installer:

1. Run: `python installation/debug_framework_installer.py` or double-click `installation/run_installer.bat`
2. Follow the on-screen instructions
3. The installer will:
   - Install required Python packages
   - Configure environment variables
   - Set up TeraTerm
   - Validate the installation

For complete details, see **[INSTALLER_README.md](installation/INSTALLER_README.md)**

---

## �📚 Documentation Index

### Getting Started

1. **[INSTALLER_README.md](installation/INSTALLER_README.md)** ⭐ **START HERE - Quick Start**
   - Quick installation guide
   - Automated installer usage
   - Troubleshooting tips
   - What to do after installation

2. **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - **Complete Reference**
   - Detailed installation instructions
   - Environment configuration
   - System requirements
   - Advanced setup options

### User Manuals

2. **[THR_DEBUG_FRAMEWORK_USER_MANUAL.md](THR_DEBUG_FRAMEWORK_USER_MANUAL.md)**
   - Comprehensive framework documentation
   - All modules and interfaces
   - Detailed function reference
   - Troubleshooting guide

### Quick References

3. **[MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md](MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md)** ⭐ **NEW in v1.7**
   - MDT tools interface usage
   - TOR dump generation
   - Register/fuse dumps
   - Common workflows

4. **[FUSE_FILE_QUICK_REFERENCE.md](FUSE_FILE_QUICK_REFERENCE.md)**
   - External .fuse file format
   - Syntax and examples
   - Product-specific hierarchies
   - Integration methods

5. **[THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md](THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md)**
   - File naming conventions
   - Import paths for all products
   - Architecture differences
   - Migration guide

### Interactive Examples

6. **[THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb)**
   - Jupyter notebook with DebugFramework examples
   - Control Panel, Automation Panel
   - Quick Test GUIs
   - Live code demonstrations

7. **[THR_S2T_EXAMPLES.ipynb](THR_S2T_EXAMPLES.ipynb)**
   - S2T and dpmChecks examples
   - Logger, pseudo_bs
   - Fuse operations
   - Real-world scenarios

---

## 🚀 Quick Start (New Users)

### Step 1: Installation

Run the Python GUI installer:

```powershell
cd C:\Git\Automation\S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T
python installation/debug_framework_installer.py
```

**Or** double-click `installation/debug_framework_installer.py` from Windows Explorer (or use `installation/run_installer.bat`).

For details, see: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)

### Step 2: Verify Setup

```python
# In PythonSV console
import users.gaespino.DebugFramework.GNRSystemDebug as gdf
gdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')
```

### Step 3: Launch Interface

```python
import DebugFramework.SystemDebug as sd

# Control Panel - For experiments
sd.ControlPanel()

# Or Quick Test
import S2T.SetTesterRegs as s2t
s2t.MeshQuickTest(GUI=True)
```

### Step 4: Explore Documentation

- Read: [THR_DEBUG_FRAMEWORK_USER_MANUAL.md](THR_DEBUG_FRAMEWORK_USER_MANUAL.md)
- Try: [THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb)

---

## 🆕 What's New in Version 1.7

### 1. Python GUI Installer

- **Visual interface installer** - Complete system setup with real-time progress
- **Environment variable automation** - No manual TTL editing
- **Dependency validation** - Automatic package checking
- **System health checks** - Built-in verification tools
- **Flexible configuration** - Enable/disable installation steps

### 2. MDT Tools Interface

- **TOR dump generation** - Debug memory transactions
- **Component access** - CCF, PM, XBAR, cache, and more
- **Performance optimized** - Load only needed components
- **Cross-product support** - DMR, GNR, CWF

```python
import S2T.dpmChecks as dpm

# Quick TOR dump
dpm.tor_dump(visual_id='test_001')

# Advanced usage
mdt = dpm.mdt_tools()
mdt.print_available_components()
```

### 3. Register/Fuse Dumps

- **Comprehensive dumps** - All register values to CSV/Excel
- **Baseline documentation** - Capture known-good configs
- **Comparison workflows** - Compare unit configurations
- **Fuse file generation** - Export to .fuse format

```python
import S2T.dpmChecks as dpm

# Create dump
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\baseline.csv'
)
```

### 4. Enhanced Documentation

- **Complete installation guide** - Step-by-step setup
- **Quick reference cards** - Common workflows
- **Interactive examples** - Jupyter notebooks
- **Troubleshooting sections** - Common issues solved

---

## 📋 Documentation by Use Case

### I want to...

#### Install the Framework for the First Time
→ Read: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
→ Run: `python installation/debug_framework_installer.py`
→ Read: [THR_DEBUG_FRAMEWORK_USER_MANUAL.md - Quick Start](THR_DEBUG_FRAMEWORK_USER_MANUAL.md#quick-start)
→ Try: `s2t.MeshQuickTest(GUI=True)`

#### Debug a Memory Hang
→ Read: [MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md - Workflow 1](MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md#workflow-1-debug-memory-hangs)
→ Use: `dpm.tor_dump()`

#### Compare Two Units
→ Read: [MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md - Workflow 2](MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md#workflow-2-compare-two-units)
→ Use: `dpm.fuse_dump()` + pandas

#### Create Custom Fuse File
→ Read: [FUSE_FILE_QUICK_REFERENCE.md](FUSE_FILE_QUICK_REFERENCE.md)
→ Use: `dpm.process_fuse_file()` + `dpm.external_fuses()`

#### Automate Test Flows
→ Read: [THR_DEBUG_FRAMEWORK_USER_MANUAL.md - Automation Panel](THR_DEBUG_FRAMEWORK_USER_MANUAL.md#automation-panel)
→ Launch: `sd.AutomationPanel()`

#### Capture Unit Baseline
→ Read: [MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md - Workflow 4](MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md#workflow-4-baseline-documentation)
→ Dump: All dies with `dpm.fuse_dump()`

#### Log MCA Errors
→ Read: [THR_DEBUG_FRAMEWORK_USER_MANUAL.md - dpmChecks](THR_DEBUG_FRAMEWORK_USER_MANUAL.md#dpmchecks-module)
→ Use: `dpm.logger()`

#### Boot with Custom Configuration
→ Read: [THR_DEBUG_FRAMEWORK_USER_MANUAL.md - Pseudo BS](THR_DEBUG_FRAMEWORK_USER_MANUAL.md#pseudo-bootscript)
→ Use: `dpm.pseudo_bs()`

---

## 🏗️ Framework Architecture

### Products Supported

| Product | Code | Framework | Architecture |
|---------|------|-----------|--------------|
| Granite Rapids | GNR | BASELINE | Compute-based |
| Clearwater Forest | CWF | BASELINE | Compute-based |
| Diamond Rapids | DMR | BASELINE_DMR | CBB-based |

### Module Structure

```
DebugFramework/
├── SystemDebug.py          # Main interface (Control/Automation Panels)
├── CoreManipulation.py     # Core/slice masking, bootscripts
├── DffDataCollector.py     # DFF data collection
├── GetTesterCurves.py      # Curve extraction
└── UI/                     # GUI components

S2T/
├── dpmChecks.py           # Core S2T functions (logger, pseudo_bs, MDT tools)
├── SetTesterRegs.py       # Quick test GUIs
├── ConfigsLoader.py       # Product configuration
├── Tools/
│   ├── debugtools.py      # MDT tools wrapper
│   ├── registerdump.py    # Fuse dump engine
│   └── FuseFileGen/       # Fuse file generators
└── product_specific/      # Product-specific implementations
```

### Key Components

| Component | Purpose | Primary Functions |
|-----------|---------|-------------------|
| **SystemDebug** | User interfaces | ControlPanel, AutomationPanel, DebugMask |
| **SetTesterRegs** | Quick testing | MeshQuickTest, SliceQuickTest |
| **dpmChecks** | Core operations | logger, pseudo_bs, mdt_tools, fuse_dump |
| **CoreManipulation** | Core control | mask_fuse_core_array, go_to_efi |
| **GetTesterCurves** | DFF data | dump_uncore_curves |

---

## 🛠️ Installation Files

### Python GUI Installer

- **`installation/debug_framework_installer.py`** - Main installer with graphical interface
  - Visual progress tracking
  - Checks Python installation
  - Installs all dependencies
  - Configures environment variables
  - Sets up TeraTerm
  - Copies EFI content (optional)
  - Validates installation
  - Real-time logging

### Configuration Scripts

- **`installation/TeratermEnv.ps1`** - PowerShell environment setup
  - Sets COM port and IP variables
  - Validates TeraTerm installation
  - Creates verification tools

### Configuration Options

The installer provides configurable options:
- Enable/disable dependency installation
- Enable/disable environment variable setup
- Enable/disable TeraTerm configuration
- Optional EFI content copy with path selection

See: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for details

---

## 🔗 External Resources

### Network Locations

| Resource | Path |
|----------|------|
| Configuration Files | `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\ConfigFiles\` |
| GNR Templates | `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\GNR\` |
| CWF Templates | `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\CWF\` |
| DMR Templates | `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\DMR\` |

### Source Code Repositories

- **GNR:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.graniterapids
- **CWF:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.clearwaterforest
- **DMR:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.diamondrapids

### Internal Documentation

- **Repository:** `c:\Git\Automation\S2T\`
- **Documentation:** `c:\Git\Automation\S2T\DOCUMENTATION\`

---

## 📦 Required Dependencies

### Python Packages

From `requirements.txt`:
- pandas >= 1.3.0
- numpy >= 1.21.0
- openpyxl >= 3.0.0
- xlwings >= 0.24.0
- pymongo >= 3.12.0
- colorama >= 0.4.4
- tabulate >= 0.8.9
- pytz >= 2021.1
- psutil >= 5.8.0
- lxml >= 4.6.3

Additional:
- zeep (for SOAP operations)

### System Requirements

- Python 3.8+
- PythonSV environment
- TeraTerm
- Microsoft Excel (for xlwings)
- Windows 10/11 or Windows Server

---

## 📝 Quick Command Reference

### Import Framework

```python
import sys
sys.path.append(r'C:\Git\Automation\S2T\BASELINE')  # GNR/CWF
# sys.path.append(r'C:\Git\Automation\S2T\BASELINE_DMR')  # DMR

import DebugFramework.SystemDebug as sd
import S2T.SetTesterRegs as s2t
import S2T.dpmChecks as dpm
import S2T.CoreManipulation as gcm
```

### Launch Interfaces

```python
sd.ControlPanel()              # Experiment control
sd.AutomationPanel()           # Flow automation
sd.DebugMask()                 # Mask editor
s2t.MeshQuickTest(GUI=True)    # Quick mesh test
s2t.SliceQuickTest(GUI=True)   # Quick slice test
```

### Common Operations

```python
# Logger
dpm.logger(visual='U0042', TestName='mesh', Testnumber=1)

# Pseudo bootscript
dpm.pseudo_bs(ClassMask='FirstPass', boot=True)

# TOR dump (v1.7+)
dpm.tor_dump(visual_id='test_001')

# Fuse dump (v1.7+)
dpm.fuse_dump(base=sv.socket0.cbb0.base.fuses, file_path='C:\\Temp\\dump.csv')

# External fuse file
fuses = dpm.process_fuse_file('C:\\Temp\\config.fuse')
config = dpm.external_fuses(external_fuses=fuses, bsformat=True)
dpm.pseudo_bs(ClassMask='FirstPass', fuse_cbb=config, boot=True)
```

---

## 💡 Tips & Best Practices

### 1. Always Update First

```bash
cd C:\Git\Automation\S2T
git pull origin main
```

### 2. Restart PythonSV After Env Changes

Close and reopen PythonSV after:
- Installing new packages
- Changing environment variables
- Running installers

### 3. Use Descriptive IDs

```python
# Good
visual_id = f"{product}_{unit_id}_{test_name}_{timestamp}"

# Avoid
visual_id = "test1"
```

### 4. Organize Output Files

```python
import os
unit_dir = f'C:\\Debug\\{unit_id}'
os.makedirs(unit_dir, exist_ok=True)
```

### 5. Document Baselines

Store baseline dumps in version control for team reference.

---

## 🐛 Troubleshooting

### Common Issues

1. **Import errors** → Check sys.path, verify installation
2. **Environment variables not loading** → Restart PythonSV
3. **TeraTerm not found** → Run installation/TeratermEnv.ps1
4. **Package missing** → Run `pip install <package>`
5. **Permission denied** → Run as Administrator

See: [INSTALLATION_GUIDE.md - Troubleshooting](INSTALLATION_GUIDE.md#troubleshooting)

---

## 📧 Support

**Primary Maintainer:**
- Gabriel Espinoza
- gabriel.espinoza.ballestero@intel.com

**For Technical Support:**
- Questions: Contact maintainer via email
- Bug reports: Include framework version, product, full error logs
- Feature requests: Provide detailed use case description

---

## 📅 Version History

| Version | Date | Highlights |
|---------|------|------------|
| **1.7** | Feb 16, 2026 | ⭐ Automated installation, MDT tools, fuse dumps |
| 2.0 | Jan 15, 2026 | Unified manual for all products |
| 1.0 | Jan 1, 2026 | Initial framework release |

---

## 📄 License & Classification

**© 2026 Intel Corporation. Intel Confidential.**

This documentation and associated software are proprietary to Intel Corporation and are provided under Intel's standard license agreements.

---

**Last Updated:** February 16, 2026
**Documentation Version:** 1.7
**Framework Version:** 1.7
