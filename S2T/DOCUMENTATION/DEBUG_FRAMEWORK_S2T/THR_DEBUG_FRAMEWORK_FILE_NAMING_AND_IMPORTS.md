# BASELINE Framework - File Naming and Import Paths

**Version:** 2.0
**Release Date:** January 15, 2026
**Organization:** Intel Corporation - Test & Validation
**Classification:** Intel Confidential
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)
**Products:** GNR (Granite Rapids), CWF (Clearwater Forest), DMR (Diamond Rapids)
**Repository:** `c:\Git\Automation\S2T\`
**Documentation:** `c:\Git\Automation\S2T\DOCUMENTATION\`

---

## Overview

This document defines the file naming conventions and import paths for the BASELINE Framework across all supported products.

---

## Import Path Structure

### Path Locations by Product

| Product | DebugFramework Path | S2T Path |
|---------|-------------------|----------|
| **GNR (Granite Rapids)** | `users.gaespino.DebugFramework` | `users.THR.PythonScripts.thr.S2T` |
| **CWF (Clearwater Forest)** | `users.gaespino.DebugFramework` | `users.THR.PythonScripts.thr.S2T` |
| **DMR (Diamond Rapids)** | `users.THR.dmr_debug_utilities.DebugFramework` | `users.THR.dmr_debug_utilities.S2T` |
| **Next Gen** | `users.THR.dmr_debug_utilities.DebugFramework` | `users.THR.dmr_debug_utilities.S2T` |

### Import Examples

#### GNR
```python
import users.gaespino.DebugFramework.GNRSystemDebug as sd
import users.THR.PythonScripts.thr.S2T.GNRSetTesterRegs as s2t
import users.THR.PythonScripts.thr.S2T.GNRCoreManipulation as gcm
import users.THR.PythonScripts.thr.S2T.dpmChecksGNR as dpm
import users.THR.PythonScripts.thr.S2T.GNRGetTesterCurves as gtc
import users.THR.PythonScripts.thr.S2T.GNRDffDataCollector as dfc
```

#### CWF
```python
import users.gaespino.DebugFramework.CWFSystemDebug as sd
import users.THR.PythonScripts.thr.S2T.CWFSetTesterRegs as s2t
import users.THR.PythonScripts.thr.S2T.CWFCoreManipulation as gcm
import users.THR.PythonScripts.thr.S2T.dpmChecksCWF as dpm
import users.THR.PythonScripts.thr.S2T.CWFGetTesterCurves as gtc
import users.THR.PythonScripts.thr.S2T.CWFDffDataCollector as dfc
```

#### DMR
```python
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd
import users.THR.dmr_debug_utilities.S2T.SetTesterRegs as s2t
import users.THR.dmr_debug_utilities.S2T.CoreManipulation as gcm
import users.THR.dmr_debug_utilities.S2T.dpmChecks as dpm
import users.THR.dmr_debug_utilities.S2T.GetTesterCurves as gtc
import users.THR.dmr_debug_utilities.S2T.DffDataCollector as dfc
```

---

## File Naming Convention

### Naming Rules

| Product | Convention | Example |
|---------|-----------|---------|
| **GNR** | `GNR` prefix | `GNRSystemDebug.py` |
| **CWF** | `CWF` prefix | `CWFSystemDebug.py` |
| **DMR** | No prefix | `SystemDebug.py` |
| **Next Gen** | No prefix | `SystemDebug.py` |

> **Key Rule:** GNR and CWF files have product prefixes. DMR and all future products use base names without prefixes.

---

## Complete File Name Reference

### DebugFramework Module Files

| Module | GNR File | CWF File | DMR File |
|--------|----------|----------|----------|
| **SystemDebug** | `GNRSystemDebug.py` | `CWFSystemDebug.py` | `SystemDebug.py` |
| **MaskEditor** | `GNRMaskEditor.py` | `CWFMaskEditor.py` | `MaskEditor.py` |

### S2T Module Files

| Module | GNR File | CWF File | DMR File |
|--------|----------|----------|----------|
| **SetTesterRegs** | `GNRSetTesterRegs.py` | `CWFSetTesterRegs.py` | `SetTesterRegs.py` |
| **CoreManipulation** | `GNRCoreManipulation.py` | `CWFCoreManipulation.py` | `CoreManipulation.py` |
| **dpmChecks** | `dpmChecksGNR.py` | `dpmChecksCWF.py` | `dpmChecks.py` |
| **GetTesterCurves** | `GNRGetTesterCurves.py` | `CWFGetTesterCurves.py` | `GetTesterCurves.py` |
| **DffDataCollector** | `GNRDffDataCollector.py` | `CWFDffDataCollector.py` | `DffDataCollector.py` |

---

## Framework Structure with File Names

```
users.gaespino.DebugFramework/          # GNR/CWF DebugFramework location
│   ├── GNRSystemDebug.py               # GNR main entry
│   ├── CWFSystemDebug.py               # CWF main entry
│   ├── GNRMaskEditor.py                # GNR mask editor
│   ├── CWFMaskEditor.py                # CWF mask editor
│   ├── UI/
│   │   ├── ControlPanel.py
│   │   └── AutomationPanel.py
│   ├── Automation_Flow/
│   └── ExecutionHandler/

users.THR.PythonScripts.thr.S2T/        # GNR/CWF S2T location
│   ├── GNRSetTesterRegs.py             # GNR S2T main
│   ├── CWFSetTesterRegs.py             # CWF S2T main
│   ├── GNRCoreManipulation.py          # GNR core manipulation
│   ├── CWFCoreManipulation.py          # CWF core manipulation
│   ├── dpmChecksGNR.py                 # GNR dpmChecks
│   ├── dpmChecksCWF.py                 # CWF dpmChecks
│   ├── GNRGetTesterCurves.py           # GNR curves
│   ├── CWFGetTesterCurves.py           # CWF curves
│   ├── GNRDffDataCollector.py          # GNR DFF
│   └── CWFDffDataCollector.py          # CWF DFF

users.THR.dmr_debug_utilities.DebugFramework/  # DMR DebugFramework location
│   ├── SystemDebug.py                  # DMR main (no prefix)
│   ├── MaskEditor.py                   # DMR mask editor (no prefix)
│   ├── UI/
│   │   ├── ControlPanel.py
│   │   └── AutomationPanel.py
│   ├── Automation_Flow/
│   └── ExecutionHandler/

users.THR.dmr_debug_utilities.S2T/      # DMR S2T location
│   ├── SetTesterRegs.py                # DMR S2T main (no prefix)
│   ├── CoreManipulation.py             # DMR core manipulation (no prefix)
│   ├── dpmChecks.py                    # DMR dpmChecks (no prefix)
│   ├── GetTesterCurves.py              # DMR curves (no prefix)
│   └── DffDataCollector.py             # DMR DFF (no prefix)
```

---

## Function Call Examples

### All Products Use Same Function Names

Despite different file names, all products use **identical function calls**:

```python
# Control Panel - Works on all products
sd.ControlPanel()

# Automation Panel - Works on all products
sd.AutomationPanel()

# Mesh Quick Test - Works on all products
s2t.MeshQuickTest()

# Slice Quick Test - Works on all products
s2t.SliceQuickTest()

# S2T Console - Works on all products
s2t.setupSystemAsTester()

# Logger - Works on all products
dpm.logger(visual='74GC556700043', TestName='Test1')

# Pseudo bootscript - Works on all products
dpm.pseudo_bs(ClassMask='FirstPass', boot=True)
```

---

## Quick Reference Table

### Import Aliases by Product

| Alias | GNR Import | CWF Import | DMR Import |
|-------|-----------|-----------|-----------|
| `sd` | `DebugFramework.GNRSystemDebug` | `DebugFramework.CWFSystemDebug` | `DebugFramework.SystemDebug` |
| `s2t` | `S2T.GNRSetTesterRegs` | `S2T.CWFSetTesterRegs` | `S2T.SetTesterRegs` |
| `gcm` | `S2T.GNRCoreManipulation` | `S2T.CWFCoreManipulation` | `S2T.CoreManipulation` |
| `dpm` | `S2T.dpmChecksGNR` | `S2T.dpmChecksCWF` | `S2T.dpmChecks` |
| `gtc` | `S2T.GNRGetTesterCurves` | `S2T.CWFGetTesterCurves` | `S2T.GetTesterCurves` |
| `dfc` | `S2T.GNRDffDataCollector` | `S2T.CWFDffDataCollector` | `S2T.DffDataCollector` |

---

## Source Code Repositories

The framework code is maintained in separate GitHub repositories by product:

### GNR (Granite Rapids)
**Repository:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.graniterapids

**Import Paths:**
- DebugFramework: `users.gaespino.DebugFramework`
- S2T: `users.THR.PythonScripts.thr.S2T`

### CWF (Clearwater Forest)
**Repository:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.clearwaterforest

**Import Paths:**
- DebugFramework: `users.gaespino.DebugFramework`
- S2T: `users.THR.PythonScripts.thr.S2T`

### DMR (Diamond Rapids)
**Repository:** https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.diamondrapids

**Import Paths:**
- DebugFramework: `users.THR.dmr_debug_utilities.DebugFramework`
- S2T: `users.THR.dmr_debug_utilities.S2T`

---

## Best Practices

### 1. Use Product-Specific Imports
Always import the correct product-specific module with full path:
```python
# ✓ CORRECT for GNR
import users.gaespino.DebugFramework.GNRSystemDebug as sd

# ✗ WRONG for GNR
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd  # This is for DMR only!
```

### 2. Consistent Alias Names
Use standard alias names across all scripts:
```python
import users.gaespino.DebugFramework.GNRSystemDebug as sd                 # Always 'sd'
import users.THR.PythonScripts.thr.S2T.GNRSetTesterRegs as s2t           # Always 's2t'
import users.THR.PythonScripts.thr.S2T.GNRCoreManipulation as gcm        # Always 'gcm'
import users.THR.PythonScripts.thr.S2T.dpmChecksGNR as dpm               # Always 'dpm'
```

### 3. Comment Your Product
Always comment which product your script is for:
```python
# GNR Product Script
import users.gaespino.DebugFramework.GNRSystemDebug as sd
import users.THR.PythonScripts.thr.S2T.GNRSetTesterRegs as s2t
```

### 4. Write Product-Agnostic Code
After imports, write code that works on any product:
```python
# This code works identically on all products
sd.ControlPanel()
s2t.MeshQuickTest(core_freq=2.5, mesh_freq=2.0)
dpm.logger(visual='74GC556700043', TestName='Test1')
```

---

## Troubleshooting

### Import Error - Module Not Found

**Problem:**
```
ModuleNotFoundError: No module named 'users.gaespino.DebugFramework.SystemDebug'
```

**Solution:** Check you're using the correct product-specific module name with full path:
- GNR: `users.gaespino.DebugFramework.GNRSystemDebug` not `SystemDebug`
- CWF: `users.gaespino.DebugFramework.CWFSystemDebug` not `SystemDebug`
- DMR: `users.THR.dmr_debug_utilities.DebugFramework.SystemDebug` (no prefix)

### Wrong Product Imported

**Problem:** Script runs but shows wrong product config

**Solution:** Verify you're using the correct full import path:
- GNR/CWF: `users.gaespino.DebugFramework` and `users.THR.PythonScripts.thr.S2T`
- DMR: `users.THR.dmr_debug_utilities.DebugFramework` and `users.THR.dmr_debug_utilities.S2T`

### Repository Access Issues

**Problem:** Cannot find module on PythonSV

**Solution:** Ensure you have access to the correct GitHub repository:
- GNR: https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.graniterapids
- CWF: https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.clearwaterforest
- DMR: https://github.com/intel-restricted/frameworks.validation.pythonsv.projects.diamondrapids

---

## Documentation Files

Related documentation in `S2T/DOCUMENTATION/`:
- **THR_DEBUG_FRAMEWORK_USER_MANUAL.md** - Complete user manual for all products
- **THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb** - DebugFramework interface examples (ControlPanel, AutomationPanel, MeshQuickTest, etc.)
- **THR_S2T_EXAMPLES.ipynb** - S2T/dpmChecks module examples

---

## 📧 Support and Contact

**Maintainer:** Gabriel Espinoza
**Email:** gabriel.espinoza.ballestero@intel.com
**Organization:** Intel Corporation - Test & Validation
**Framework:** BASELINE Testing Framework v2.0
**Release Date:** January 15, 2026

**For Technical Support:**
- Questions about import paths or file naming: Contact maintainer via email
- Deployment issues: Include product (GNR/CWF/DMR) and target location
- Documentation updates: Report missing information or inconsistencies

**Related Documentation:**
- Complete User Manual: [THR_DEBUG_FRAMEWORK_USER_MANUAL.md](THR_DEBUG_FRAMEWORK_USER_MANUAL.md)
- DebugFramework Examples: [THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb)
- S2T Examples: [THR_S2T_EXAMPLES.ipynb](THR_S2T_EXAMPLES.ipynb)
- Main Documentation Index: [../README.md](THR_DOCUMENTATION_README.md)

**Repository Location:** `c:\Git\Automation\S2T\`
**Documentation Location:** `c:\Git\Automation\S2T\DOCUMENTATION\`

---

**© 2026 Intel Corporation. Intel Confidential.**
