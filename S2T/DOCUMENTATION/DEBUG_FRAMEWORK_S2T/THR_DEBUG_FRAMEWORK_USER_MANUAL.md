# BASELINE Framework - Unified User Manual

**Version:** 2.0
**Release Date:** January 15, 2026
**Organization:** Intel Corporation - Test & Validation
**Classification:** Intel Confidential
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)
**Products:** GNR (Granite Rapids), CWF (Clearwater Forest), DMR (Diamond Rapids)
**Repository:** `c:\Git\Automation\S2T\`
**Documentation:** `c:\Git\Automation\S2T\DOCUMENTATION\`

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation & Setup](#installation--setup)
4. [Quick Start](#quick-start)
5. [Framework Architecture](#framework-architecture)
6. [Main Interfaces](#main-interfaces)
7. [Core Modules](#core-modules)
8. [Common Workflows](#common-workflows)
9. [Troubleshooting](#troubleshooting)
10. [Reference](#reference)

**Additional Documentation:**
- **[THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md](THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md)** - Complete guide to file naming conventions and import paths
- **[THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb)** - Jupyter notebook with DebugFramework interface examples
- **[THR_S2T_EXAMPLES.ipynb](THR_S2T_EXAMPLES.ipynb)** - Jupyter notebook with S2T/dpmChecks examples

**Source Code Repositories:**
- **GNR:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.graniterapids
- **CWF:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.clearwaterforest
- **DMR:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.diamondrapids

---

## Introduction

The **BASELINE Framework** is Intel's comprehensive test automation and debug environment for server validation across multiple product families.

### Supported Products

| Product | Code | Framework Location | Architecture |
|---------|------|-------------------|--------------|
| **Granite Rapids** | GNR | BASELINE | COMPUTE-based |
| **Clearwater Forest** | CWF | BASELINE | COMPUTE-based |
| **Diamond Rapids** | DMR | BASELINE_DMR | CBB-based |
| **Next Generation** | TBD (Future) | BASELINE_DMR | CBB-based |

### Key Capabilities

- **Test Execution** - Loop, sweep, and shmoo testing
- **System-to-Tester (S2T)** - ATE-style testing in system environment
- **Automation Flows** - Multi-step validation sequences
- **DFF Data Management** - Unit characterization data
- **MCA Logging** - Hardware error reporting and decoding

---

## System Requirements

### Hardware
- Intel server platform (GNR/CWF/DMR)
- Serial connection (COM port)
- Network connectivity
- ITP connection

### Software
- Python 3.8+
- PythonSV (Intel Silicon Validation environment)
- IPC libraries
- Required packages: pandas, tkinter, colorama, tabulate, pytz, zeep, openpyxl

### Framework Locations

| Product | DebugFramework Location | S2T Location |
|---------|------------------------|-------------|
| **GNR** | users.gaespino.DebugFramework | users.THR.PythonScripts.thr.S2T |
| **CWF** | users.gaespino.DebugFramework | users.THR.PythonScripts.thr.S2T |
| **DMR** | users.THR.dmr_debug_utilities.DebugFramework | users.THR.dmr_debug_utilities.S2T |

### File Naming Convention

**GNR Files:**
- GNRSystemDebug.py, GNRSetTesterRegs.py, dpmChecksGNR.py
- GNRCoreManipulation.py, GNRDffDataCollector.py, GNRGetTesterCurves.py
- GNRMaskEditor.py

**CWF Files:**
- CWFSystemDebug.py, CWFSetTesterRegs.py, dpmChecksCWF.py
- CWFCoreManipulation.py, CWFDffDataCollector.py, CWFGetTesterCurves.py
- CWFMaskEditor.py

**DMR Files (no product prefix):**
- SystemDebug.py, SetTesterRegs.py, dpmChecks.py
- CoreManipulation.py, DffDataCollector.py, GetTesterCurves.py
- MaskEditor.py

### Installation

```bash
# Install dependencies
pip install -r requirements.txt --proxy http://proxy-dmz.intel.com:911/
```

---

## Quick Start

### Choose Your Product

```python
# For GNR
import users.gaespino.DebugFramework.GNRSystemDebug as sd
import users.THR.PythonScripts.thr.S2T.GNRSetTesterRegs as s2t

# For CWF
import users.gaespino.DebugFramework.CWFSystemDebug as sd
import users.THR.PythonScripts.thr.S2T.CWFSetTesterRegs as s2t

# For DMR/Next Gen
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t
```

> **Note:** Throughout this manual, code examples may show abbreviated imports for brevity. In actual use, use full paths: `users.THR.PythonScripts.thr.S2T.GNRSetTesterRegs` for GNR, `users.THR.PythonScripts.thr.S2T.CWFSetTesterRegs` for CWF, or `users.THR.dmr_debug_utilities.S2T.SetTesterRegs` for DMR.

### Launch an Interface

```python
# Control Panel - Experiment execution
sd.ControlPanel()

# Automation Panel - Flow automation
sd.AutomationPanel()

# Mesh Quick Test - Quick mesh defeature
s2t.MeshQuickTest()

# Slice Quick Test - Quick slice defeature
s2t.SliceQuickTest()

# S2T Console Menu - Full S2T configuration
s2t.setupSystemAsTester()
```

---

## Framework Architecture

### Directory Structure

```
BASELINE/ or BASELINE_DMR/
├── DebugFramework/          # Test execution framework
│   ├── SystemDebug.py       # Main entry point
│   ├── UI/                  # User interfaces
│   │   ├── ControlPanel.py
│   │   └── AutomationPanel.py
│   ├── Automation_Flow/     # Flow automation
│   └── ExecutionHandler/    # Test execution management
│
└── S2T/                     # System-to-Tester tools
    ├── SetTesterRegs.py     # Main S2T script
    ├── CoreManipulation.py  # Core/slice masking
    ├── dpmChecks.py         # DPM validation
    ├── GetTesterCurves.py   # DFF data retrieval
    └── DffDataCollector.py  # DFF batch collection
```

### Product Differences

| Aspect | GNR/CWF (BASELINE) | DMR (BASELINE_DMR) |
|--------|-------------------|-------------------|
| **Import Path** | S2T/BASELINE | S2T/BASELINE_DMR |
| **Architecture** | COMPUTE0/1/2, IO0/1 | CBB0/1/2/3 |
| **User Interface** | Identical | Identical |
| **Function Calls** | Same | Same |

**Key Point:** Only the import path changes between products. All interfaces and functions work identically.

---

## Main Interfaces

### 1. ControlPanel

**Purpose:** Execute experiments with loops, sweeps, and shmoos

**Launch:**
```python
# GNR
import DebugFramework.GNRSystemDebug as sd
sd.ControlPanel()

# CWF
import DebugFramework.CWFSystemDebug as sd
sd.ControlPanel()

# DMR
import DebugFramework.SystemDebug as sd
sd.ControlPanel()
```

**Features:**
- Load and run experiments from JSON files
- Configure loops (1-10000 iterations)
- Voltage/frequency sweeps
- 2D shmoo plots
- Real-time status monitoring
- Multiple test types: Boot, Dragon, Linux

**Configuration Options:**
- COM Port
- IP Address
- Visual ID
- Temperature
- Boot postcodes and wait times
- Bootscript retry logic

**Use Cases:**
- Repeated test execution (burn-in)
- Voltage margin testing
- Frequency validation
- Parameter exploration

**See Jupyter Notebook:** `examples_interfaces.ipynb` for detailed examples

---

### 2. AutomationPanel

**Purpose:** Execute multi-step automation flows

**Launch:**
```python
# GNR
import DebugFramework.GNRSystemDebug as sd
sd.AutomationPanel()

# CWF
import DebugFramework.CWFSystemDebug as sd
sd.AutomationPanel()

# DMR
import DebugFramework.SystemDebug as sd
sd.AutomationPanel()
```

**Features:**
- Flow-based test automation
- Sequential step execution
- Voltage sweep automation
- Parameter configuration
- Flow designer integration

**Configuration Options:**
- Visual ID
- COM Port
- IP Address
- CFC Voltage range (start, end, steps)
- IA Voltage range (start, end, steps)
- Temperature

**Flow Design:**
Flows are created using `AutomationDesigner` in the `DebugFramework/Automation_Flow/` module

**Use Cases:**
- Complex multi-step validation
- Automated voltage sweeps
- Sequential test execution
- Production test flows

**See Jupyter Notebook:** `examples_interfaces.ipynb` for detailed examples

---

### 3. MeshQuickTest

**Purpose:** Quick mesh defeature configuration and execution

**Launch:**
```python
import S2T.SetTesterRegs as s2t
s2t.MeshQuickTest()
```

**Function Signature:**
```python
def MeshQuickTest(
    core_freq=None,        # Core frequency in GHz
    mesh_freq=None,        # Mesh frequency in GHz
    vbump_core=None,       # Core voltage bump
    vbump_mesh=None,       # Mesh voltage bump
    Reset=False,           # Reset before test
    Mask=None,             # Target mask configuration
    pseudo=False,          # Pseudo bootscript mode
    dis_2CPM=None,         # Disable 2CPM
    dis_1CPM=None,         # Disable 1CPM
    GUI=True,              # Show GUI
    fastboot=True,         # Enable fast boot
    corelic=None,          # Core licensing
    volttype='vbump',      # Voltage type: 'vbump', 'fixed', 'ppvc', 'ate'
    debug=False,           # Debug mode
    boot_postcode=False,   # Boot to postcode
    extMask=None,          # External mask
    u600w=None,            # 600W unit check
    execution_state=None   # Execution state handler
)
```

**Voltage Types:**
- `'vbump'` - Voltage bump (offset from nominal)
- `'fixed'` - Fixed voltage values
- `'ppvc'` - PPVC (Process, Product, Voltage, Clock)
- `'ate'` - ATE configuration from DFF

**GUI Usage:**
1. Launch: `s2t.MeshQuickTest()`
2. Configure:
   - Core frequency
   - Mesh frequency
   - Voltage type
   - Additional options (MLC ways, row masks, etc.)
3. Click "Execute"
4. Monitor execution
5. Review results

**Programmatic Usage:**
```python
# Example: Run mesh test at 2.4 GHz core, 1.8 GHz mesh with voltage bump
s2t.MeshQuickTest(
    core_freq=2.4,
    mesh_freq=1.8,
    vbump_core=0.05,
    vbump_mesh=0.03,
    volttype='vbump',
    GUI=False
)
```

**Use Cases:**
- Full chip mesh testing
- Frequency defeature
- Voltage margin testing
- MLC way selection
- Row mask configuration

**See Jupyter Notebook:** `examples_interfaces.ipynb` for detailed examples

---

### 4. SliceQuickTest

**Purpose:** Quick slice defeature configuration for specific cores

**Launch:**
```python
import S2T.SetTesterRegs as s2t
s2t.SliceQuickTest()
```

**Function Signature:**
```python
def SliceQuickTest(
    Target_core=None,      # Target core for slice testing
    core_freq=None,        # Core frequency in GHz
    mesh_freq=None,        # Mesh frequency in GHz
    vbump_core=None,       # Core voltage bump
    vbump_mesh=None,       # Mesh voltage bump
    Reset=False,           # Reset before test
    pseudo=False,          # Pseudo bootscript mode
    dis_1CPM=None,         # Disable 1CPM
    dis_2CPM=None,         # Disable 2CPM
    GUI=True,              # Show GUI
    fastboot=True,         # Enable fast boot
    corelic=None,          # Core licensing
    volttype='fixed',      # Voltage type
    debug=False,           # Debug mode
    boot_postcode=False,   # Boot to postcode
    u600w=None,            # 600W unit check
    execution_state=None   # Execution state handler
)
```

**GUI Usage:**
1. Launch: `s2t.SliceQuickTest()`
2. Select target core
3. Configure:
   - Core frequency
   - Mesh frequency
   - Voltage settings
   - CPM options (1CPM/2CPM)
4. Click "Execute"
5. Monitor execution
6. Review results

**Programmatic Usage:**
```python
# Example: Run slice test on core 5
s2t.SliceQuickTest(
    Target_core=5,
    core_freq=2.0,
    mesh_freq=1.6,
    vbump_core=0.08,
    volttype='fixed',
    GUI=False
)
```

**Use Cases:**
- Slice content execution
- Core-specific testing
- CPM (Cores Per Module) testing
- Slice defeature validation

**See Jupyter Notebook:** `examples_interfaces.ipynb` for detailed examples

---

### 5. setupSystemAsTester

**Purpose:** Console-based full S2T configuration

**Launch:**
```python
import S2T.SetTesterRegs as s2t
s2t.setupSystemAsTester()
```

**Function Signature:**
```python
def setupSystemAsTester(debug=False)
```

**Menu Options:**
1. **SLICE Mode** - Configure slice testing
2. **MESH Mode** - Configure mesh testing

**Interactive Process:**
- Select mode (Slice or Mesh)
- Answer configuration questions
- System configures S2T settings
- Execute test

**Use Cases:**
- Full S2T configuration control
- Console-based automation
- Detailed parameter setting
- Advanced S2T options

**See Jupyter Notebook:** `examples_interfaces.ipynb` for detailed examples

---

## Core Modules

### SystemDebug Module

**File:** `DebugFramework/SystemDebug.py`

**Main Functions:**

```python
import DebugFramework.SystemDebug as sd

# Launch interfaces
sd.ControlPanel()              # Control Panel GUI
sd.AutomationPanel()           # Automation Panel GUI

# Utility functions
sd.DebugMask()                 # Core/slice mask editor
sd.enable_debug_logging(file)  # Enable debug logging
sd.disable_debug_logging()     # Disable debug logging
sd.get_debug_status()          # Get logging status
```

**Debug Logging:**
```python
# Enable logging
sd.enable_debug_logging('C:\\Temp\\debug.log', console_output=True)

# Run your tests
# ...

# Check status
status = sd.get_debug_status()
print(status)

# Disable logging
sd.disable_debug_logging()
```

---

### SetTesterRegs Module

**File:** `S2T/SetTesterRegs.py`

**Main Functions:**

```python
import S2T.SetTesterRegs as s2t

# Quick Test GUIs
s2t.MeshQuickTest()            # Mesh quick test
s2t.SliceQuickTest()           # Slice quick test

# Console interface
s2t.setupSystemAsTester()      # Full S2T configuration

# Configuration management
s2t.Configs()                  # Configuration UI
```

**Actual Parameters (from code):**

**MeshQuickTest parameters:**
- `core_freq` - Core frequency
- `mesh_freq` - Mesh frequency
- `vbump_core` - Core voltage bump
- `vbump_mesh` - Mesh voltage bump
- `volttype` - 'vbump', 'fixed', 'ppvc', 'ate'
- `GUI` - Show GUI (True/False)
- `fastboot` - Enable fast boot
- `Mask` - Target tile mask
- `pseudo` - Pseudo bootscript
- `dis_1CPM`, `dis_2CPM` - CPM disable
- `Reset` - Reset before test
- `corelic` - Core licensing
- `debug` - Debug mode
- `boot_postcode` - Boot to postcode
- `extMask` - External mask
- `u600w` - 600W check
- `execution_state` - Execution state handler

**SliceQuickTest parameters:**
- `Target_core` - Target core number
- `core_freq` - Core frequency
- `mesh_freq` - Mesh frequency
- `vbump_core` - Core voltage bump
- `vbump_mesh` - Mesh voltage bump
- `volttype` - 'vbump', 'fixed', 'ppvc', 'ate'
- `GUI` - Show GUI
- `fastboot` - Enable fast boot
- `pseudo` - Pseudo bootscript
- `dis_1CPM`, `dis_2CPM` - CPM disable
- `Reset` - Reset before test
- `corelic` - Core licensing
- `debug` - Debug mode
- `boot_postcode` - Boot to postcode
- `u600w` - 600W check
- `execution_state` - Execution state handler

---

### CoreManipulation Module

**File:** `S2T/CoreManipulation.py`

**Main Functions:**

```python
import S2T.CoreManipulation as gcm

# Core/Slice masking
gcm.mask_fuse_core_array(coremask={'compute0':0x0, 'compute1':0x0, 'compute2':0x0})
gcm.mask_fuse_llc_array(slicemask={'compute0':0x0, 'compute1':0x0, 'compute2':0x0})

# Bootscript execution
gcm.fuse_cmd_override_reset(fuse_cmd_array, boot=True, s2t=False)
gcm.fuse_cmd_override_check(fuse_cmd_array, showresults=False)

# Boot control
gcm.go_to_efi()                # Boot to EFI
gcm.read_postcode()            # Read current postcode
gcm.clear_biosbreak()          # Clear BIOS break

# Core status
gcm.coresEnabled(print_cores=True, print_llcs=True)
gcm.CheckMasks(readfuse=True)

# SV status
gcm.svStatus(checkipc=True, checksvcores=True, refresh=False)
```

---

### dpmChecks Module

**File:** `S2T/dpmChecks.py`

**Main Functions:**

```python
import S2T.dpmChecks as dpm

# Logger
dpm.logger(
    visual='',           # Visual ID
    qdf='',             # QDF number
    TestName='',        # Test name
    Testnumber=0,       # Test number
    dr_dump=True,       # DR dump
    chkmem=0,           # Check memory
    debug_mca=0,        # Debug MCA
    folder=None,        # Log folder
    WW='',              # Work week
    Bucket='UNCORE',    # Test bucket
    UI=False,           # Use UI
    refresh=False,      # Refresh
    logging=None,       # Logging object
    upload_to_disk=False,     # Upload to disk
    upload_to_danta=False     # Upload to DANTA
)

# Pseudo bootscript
dpm.pseudo_bs(
    ClassMask='FirstPass',    # Class mask type
    Custom=[],                # Custom mask
    boot=True,                # Execute boot
    use_core=False,           # Use core
    htdis=True,               # Disable HT
    dis_2CPM=None,            # Disable 2CPM
    dis_1CPM=None,            # Disable 1CPM
    fuse_read=True,           # Read fuses
    s2t=False,                # S2T mode
    masks=None,               # Masks
    clusterCheck=None,        # Cluster check
    lsb=False,                # LSB
    fuse_compute=None,        # Fuse compute
    fuse_io=None,             # Fuse IO
    fast=False,               # Fast mode
    ppvcfuse=False,           # PPVC fuse
    skip_init=False,          # Skip init
    vbump={                   # Voltage bump
        'enabled': False,
        'type': ['cfc'],
        'offset': 0,
        'computes': ['compute0', 'compute1', 'compute2']
    }
)

# BIOS knobs
dpm.bsknobs(readonly=False, skipinit=False)
dpm.biosknobs(knobs={}, readonly=False)

# Fuses
dpm.fuses(rdFuses=True, sktnum=[0], printFuse=False)
dpm.fuseRAM(refresh=False)

# Unit info
dpm.visual_str()             # Get visual ID string
dpm.qdf_str()               # Get QDF string
dpm.product_str()           # Get product string

# Hardware checks
dpm.u600w(check=True)        # Check 600W unit
dpm.reset_600w()            # Reset 600W unit
dpm.hwls_miscompare()       # Check HWLS miscompare
```

**See Jupyter Notebook:** `examples_dpmchecks.ipynb` for detailed examples

---

### GetTesterCurves Module

**File:** `S2T/GetTesterCurves.py`

**Main Functions:**

```python
import S2T.GetTesterCurves as gtc

# Initialize for product
gtc.set_variables(product='GNR', config=None)  # or 'CWF', 'DMR'

# Get DFF curves
curves = gtc.dump_uncore_curves(
    visual='74GC556700043',
    hot=True,
    usedata=True,
    custom=False,
    temp="HSTC_V"
)

# Access specific values
cfc_voltage = curves['COMPUTE0-CFC-F4-Voltage']
hdc_voltage = curves['COMPUTE0-HDC-F4-Voltage']
```

---

### DffDataCollector Module

**File:** `S2T/DffDataCollector.py`

**Main Functions:**

```python
import S2T.DffDataCollector as dfc

# Create collector
collector = dfc.datacollector()

# Collect uncore data
collector.uncore_collect(
    vidfile='C:\\Temp\\units.txt',      # File with Visual IDs
    outputfile='C:\\Temp\\output.xlsx',  # Output Excel file
    flow=['hot', 'cold']                 # Temperature flows
)

# Collect core data
collector.core_collect(
    vidfile='C:\\Temp\\units.txt',
    outputfile='C:\\Temp\\core_output.xlsx'
)
```

---

## Common Workflows

### Workflow 1: Run Experiment with Control Panel

```python
import sys
sys.path.append(r'C:\Git\Automation\S2T\BASELINE')  # or BASELINE_DMR
import DebugFramework.SystemDebug as sd

# Launch Control Panel
sd.ControlPanel()

# In GUI:
# 1. Configure platform (COM Port, IP, Visual ID)
# 2. Load experiment JSON
# 3. Set loop count or sweep parameters
# 4. Click "Start"
# 5. Monitor real-time status
# 6. Review logs in C:\SystemDebug\Logs\
```

### Workflow 2: Quick Mesh Test

```python
import S2T.SetTesterRegs as s2t

# GUI mode
s2t.MeshQuickTest()

# Or programmatic
s2t.MeshQuickTest(
    core_freq=2.4,
    mesh_freq=1.8,
    vbump_core=0.05,
    vbump_mesh=0.03,
    volttype='vbump',
    GUI=False
)
```

### Workflow 3: Slice Testing on Specific Core

```python
import S2T.SetTesterRegs as s2t

# GUI mode - select core in interface
s2t.SliceQuickTest()

# Or programmatic - target core 5
s2t.SliceQuickTest(
    Target_core=5,
    core_freq=2.0,
    mesh_freq=1.6,
    volttype='fixed',
    GUI=False
)
```

### Workflow 4: DFF Data Collection

```python
import S2T.DffDataCollector as dfc

# Create unit list file
# File: C:\Temp\units.txt
# Content: One Visual ID per line

# Collect data
collector = dfc.datacollector()
collector.uncore_collect(
    'C:\\Temp\\units.txt',
    'C:\\Temp\\results.xlsx',
    ['hot', 'cold']
)

# Open Excel file to analyze results
```

### Workflow 5: Execute Automation Flow

```python
import DebugFramework.SystemDebug as sd

# Launch Automation Panel
sd.AutomationPanel()

# In GUI:
# 1. Load flow JSON
# 2. Configure Visual ID, COM Port, IP
# 3. Set voltage sweep ranges
# 4. Set temperature
# 5. Click "Start"
# 6. Flow executes automatically
```

### Workflow 6: Logger with MCA Capture

```python
import S2T.dpmChecks as dpm

# Initialize logger
dpm.logger(
    visual='74GC556700043',
    qdf='Q12345',
    TestName='MeshDefeature',
    Testnumber=1,
    dr_dump=True,
    debug_mca=1,
    Bucket='UNCORE',
    UI=True
)

# Run your test
# ...

# Logger captures MCA errors automatically
# Reports generated in C:\SystemDebug\Logs\MCA_Reports\
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem:** Cannot import modules

**Solution:**
```python
import sys
# Add correct path
sys.path.append(r'C:\Git\Automation\S2T\BASELINE')  # or BASELINE_DMR

# Verify path
print(sys.path)
```

#### 2. Serial Connection Failed
**Problem:** Cannot connect to COM port

**Solutions:**
- Verify COM port number in Device Manager
- Check no other application is using the port
- Ensure serial cable is connected
- Try different COM port

#### 3. Bootscript Timeout
**Problem:** Bootscript times out

**Solutions:**
- Increase wait times in Control Panel
- Check platform power state
- Verify ITP connection
- Check BIOS settings

#### 4. GUI Won't Launch
**Problem:** Control Panel or Automation Panel won't open

**Solutions:**
- Check tkinter installation
- Restart PythonSV console
- Check for error messages in console
- Verify display settings

#### 5. DFF Data Not Found
**Problem:** Cannot retrieve DFF curves

**Solutions:**
- Verify Visual ID format
- Check DFF database access
- Ensure proxy settings correct
- Verify unit has DFF data uploaded

### Debug Logging

Enable comprehensive debug logging:

```python
import DebugFramework.SystemDebug as sd

# Enable logging
sd.enable_debug_logging('C:\\Temp\\debug.log', console_output=True)

# Run your test
# ...

# Review log
# C:\Temp\debug.log

# Disable when done
sd.disable_debug_logging()
```

### Log File Locations

| Type | Location |
|------|----------|
| Framework logs | C:\SystemDebug\Logs\ |
| Debug logs | C:\Temp\ |
| PythonSV console | C:\Temp\PythonSVLog.log |
| MCA reports | C:\SystemDebug\Logs\MCA_Reports\ |
| S2T configs | C:\Temp\s2t_config_*.json |
| DFF data | C:\Temp\*_vmin_dump.xlsx |

---

## Reference

### Import Quick Reference

```python
import sys

# Choose product
sys.path.append(r'C:\Git\Automation\S2T\BASELINE')      # GNR/CWF
sys.path.append(r'C:\Git\Automation\S2T\BASELINE_DMR')  # DMR

# Main modules
import DebugFramework.SystemDebug as sd
import S2T.SetTesterRegs as s2t
import S2T.CoreManipulation as gcm
import S2T.dpmChecks as dpm
import S2T.GetTesterCurves as gtc
import S2T.DffDataCollector as dfc
```

### Function Summary

| Module | Function | Purpose |
|--------|----------|---------|
| SystemDebug | `ControlPanel()` | Launch experiment control |
| SystemDebug | `AutomationPanel()` | Launch flow automation |
| SystemDebug | `DebugMask()` | Core/slice mask editor |
| SystemDebug | `enable_debug_logging()` | Enable debug logs |
| SetTesterRegs | `MeshQuickTest()` | Quick mesh test GUI |
| SetTesterRegs | `SliceQuickTest()` | Quick slice test GUI |
| SetTesterRegs | `setupSystemAsTester()` | Full S2T console |
| dpmChecks | `logger()` | MCA logging |
| dpmChecks | `pseudo_bs()` | Pseudo bootscript |
| dpmChecks | `bsknobs()` | BIOS knobs check |
| CoreManipulation | `mask_fuse_core_array()` | Core masking |
| CoreManipulation | `mask_fuse_llc_array()` | Slice masking |
| CoreManipulation | `go_to_efi()` | Boot to EFI |
| GetTesterCurves | `dump_uncore_curves()` | Get DFF curves |
| DffDataCollector | `uncore_collect()` | Batch DFF collection |

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `requirements.txt` | BASELINE/ | Python dependencies |
| `*Config.json` | DebugFramework/UI/ | UI configurations |
| `Flows.json` | DebugFramework/Automation_Flow/ | Automation flows |
| `s2t_config_*.json` | C:\Temp\ | S2T configurations |

### Product Configuration

The framework automatically detects your product through `ConfigsLoader.py`:

```python
import S2T.ConfigsLoader as cfl
product = cfl.config.SELECTED_PRODUCT  # 'GNR', 'CWF', or 'DMR'
```

**Architecture Differences:**

| Product | Structure | Domains |
|---------|-----------|---------|
| GNR/CWF | COMPUTE0/1/2, IO0/1 | compute-based |
| DMR | CBB0/1/2/3 | cbb-based |

**User Impact:** None - handled automatically by framework

---

## Examples

For detailed code examples and interactive demonstrations, see the Jupyter notebooks:

- **`examples_interfaces.ipynb`** - Control Panel, Automation Panel, MeshQuickTest, SliceQuickTest, setupSystemAsTester
- **`examples_dpmchecks.ipynb`** - logger, pseudo_bs, BIOS knobs, and other dpmChecks functions

---

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | Jan 15, 2026 | Unified manual for all products |
| 1.0 | Jan 15, 2026 | Initial documentation |

---

## 📧 Support and Contact

**Maintainer:** Gabriel Espinoza
**Email:** gabriel.espinoza.ballestero@intel.com
**Organization:** Intel Corporation - Test & Validation
**Framework:** BASELINE Testing Framework v2.0
**Release Date:** January 15, 2026

**For Technical Support:**
- Questions, issues, or clarifications: Contact maintainer via email
- Bug reports: Include framework version, product (GNR/CWF/DMR), and full error logs
- Feature requests: Provide detailed use case description and business justification
- Documentation feedback: Report errors, suggest improvements, or request additional examples

**Related Documentation:**
- File Naming & Imports: [THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md](THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md)
- DebugFramework Examples: [THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb)
- S2T/dpmChecks Examples: [THR_S2T_EXAMPLES.ipynb](THR_S2T_EXAMPLES.ipynb)
- Main Documentation Index: [../README.md](THR_DOCUMENTATION_README.md)

**Source Code Repositories:**
- **GNR:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.graniterapids
- **CWF:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.clearwaterforest
- **DMR:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.diamondrapids

**Repository Location:** `c:\Git\Automation\S2T\`
**Documentation Location:** `c:\Git\Automation\S2T\DOCUMENTATION\`

---

**© 2026 Intel Corporation. Intel Confidential.**
