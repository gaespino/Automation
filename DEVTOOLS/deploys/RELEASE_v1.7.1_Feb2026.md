# Debug Framework Release v1.7.1 - February 2026

## Release Information

- **Version:** 1.7.1
- **Release Date:** February 19, 2026
- **Previous Version:** 2.0 (January 22, 2026)
- **Products:** GNR (Granite Rapids), CWF (Clearwater Forest), DMR (Diamond Rapids)
- **Repositories:** BASELINE (GNR/CWF), BASELINE_DMR (DMR)

> **Note:** Version numbering changed from v2.0 to v1.7.1 to align with documentation versioning conventions.

---

## Overview

Debug Framework v1.7.1 introduces major improvements in installation automation, hardware debugging capabilities, and DMR-specific architecture support. This release focuses on user experience enhancements with encrypted credential management, MDT tools integration, and comprehensive bug fixes for status tracking and progress reporting.

---

## 🆕 NEW FEATURES

### 1. Automated GUI Installer with Encrypted Credentials [Common: GNR/CWF/DMR]

**Version:** 1.7.1 (February 17, 2026)
**Location:** `S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/installation/`

A complete installation automation system with professional dark-mode GUI interface.

**Key Components:**
- `scripts/debug_framework_installer.py` - Main GUI installer
- `scripts/credentials_manager.py` - Credential encryption utility
- `scripts/TeratermEnv.ps1` - Environment variable setup
- `run_installer.bat` - One-click launcher

**Features:**
- ✅ **AES-256 Encrypted Credential Storage** - Secure `credentials.enc` file with no manual password entry required
- ✅ **Automatic Environment Variables** - Sets up TeraTerm paths and serial ports
- ✅ **SSH/SCP Transfer Support** - Automated file transfer for Linux-booted units
- ✅ **Product-Based Defaults** - Pre-configured settings for GNR, CWF, and DMR
- ✅ **Verbose Logging** - Detailed installation logs for troubleshooting
- ✅ **Professional Dark Mode UI** - Modern interface with progress tracking

**Quick Start:**
```bash
run_installer.bat
```

**Documentation:**
- [Installation Guide v1.7.1](S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/INSTALLATION_GUIDE.md)
- [Credentials Setup Guide](S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/installation/docs/CREDENTIALS_SETUP.md)
- [Installation README](S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/installation/README.md)

---

### 2. MDT Tools Interface [DMR Primary, GNR/CWF Support]

**Version:** 1.7+ (February 16, 2026)
**Location:** `S2T/BASELINE_DMR/S2T/Tools/debugtools.py`

A comprehensive hardware debugging interface providing access to 41 debug components through a unified API.

**Components Available:**
- CCF (Common Coherent Fabric)
- Cache subsystem
- FIVR (Fully Integrated Voltage Regulator)
- Power Management (pm)
- Crossbar (xbar)
- And 36+ additional modules

**New Functions in `dpmChecks.py`:**
- `tor_dump()` - Generate Transaction Ordering Ring dumps from CCF
- `fuse_dump()` - Export complete register and fuse values
- `mdt_tools()` - Access and initialize debug module components

**Usage Example:**
```python
import dpmChecks as dpm

# Initialize MDT tools
tools = dpm.mdt_tools()

# Generate TOR dump
dpm.tor_dump()

# Export fuse registers
dpm.fuse_dump()

# Access specific component
if 'ccf' in tools:
    tools['ccf'].some_debug_function()
```

**Documentation:**
- [MDT Tools Quick Reference](S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md)
- [Debug Tools README](S2T/BASELINE_DMR/S2T/Tools/README_debugtools.md)

---

### 3. DMR MaskEditor Architecture Migration [DMR Only]

**Date:** Post-January 22, 2026
**Location:** `S2T/BASELINE_DMR/DebugFramework/MaskEditor.py`

Complete redesign of the masking interface to support DMR's CBB (Compute Building Block) architecture.

**Architecture Changes:**
| Aspect | GNR/CWF (Old) | DMR (New) |
|--------|--------------|-----------|
| **Structure** | Compute-based | CBB-based |
| **Units** | 3 Computes | 4 CBBs |
| **Mask Size** | 60-bit (64 hex chars) | 32-bit (8 hex chars) |
| **UI Grid** | 7×10 layout | 8×4 layout |
| **Terminology** | Core/CHA | Module/LLC |
| **Dictionary Keys** | `ia_compute_N`, `llc_compute_N` | `ia_cbbN`, `llc_cbbN` |

**UI Improvements:**
- 8×4 grid matches DMR tileview architecture
- Column-first indexing (DCM0=0-7, DCM1=8-15, DCM2=16-23, DCM3=24-31)
- Simplified layout without special MC/SPK positions
- Support for DMR chop detection (X1, X2, X3, X4)
- AP vs SP variant awareness

**Documentation:**
- [MaskEditor DMR Migration Guide](https://github.com/gaespino/Automation/blob/main/S2T/BASELINE_DMR/DebugFramework/MASKEDITOR_DMR_MIGRATION.md) ⭐ **NEW**
- [MaskEditor Visual Comparison](https://github.com/gaespino/Automation/blob/main/S2T/BASELINE_DMR/DebugFramework/MASKEDITOR_VISUAL_COMPARISON.md) ⭐ **NEW**

---

### 4. DMR Configuration Enhancements [DMR Only]

**Location:** `S2T/BASELINE_DMR/DebugFramework/ExecutionHandler/Configurations.py`

**New Field:**
- `dis1CPM: Optional[int] = None` - Added for DMR-specific configuration (line 171)

**Product-Specific Support:**
- Chop detection (X1, X2, X3, X4 based on CBB count)
- Variant detection (AP vs SP)
- CBB configuration support
- DMR-specific MCA banks (banks 0-26)
- One thread per BigCore (no SMT/HT)

**New Files:**
- `S2T/BASELINE_DMR/S2T/test_curves.py` - Testing curves functionality

---

### 5. Universal Deployment Tool v2.1.0 Enhancements [Common]

**Date:** February 2026
**Location:** `DEVTOOLS/deploy_universal.py`

**New Features:**
- Product selection (GNR, CWF, DMR) with automatic filtering
- Product-specific folder filtering (`product_specific/GNR/`, `/CWF/`, `/DMR/`)
- Configuration management with auto-save per product
- Persistent settings for each product (source type, deployment type, target, CSV, selections)

**Documentation:**
- [Universal Deployment Update Notes v2.1](https://github.com/gaespino/Automation/blob/main/DEVTOOLS/UPDATE_NOTES_v2.1.md)

---

### 6. X4 Chop Support for DMR [DMR Only]

**Date:** February 2026
**Location:** `S2T/BASELINE_DMR/S2T/SetTesterRegs.py`, `CoreManipulation.py`

**Major Enhancement:** X4 chops (all 4 CBBs) can now be used for testing on DMR platforms.

**Mesh Configurations:**
- **Computes:** Based on selection, enables same compute for all CBBs
  - Note: If a compute is already disabled on any CBB, will enable the first available instead (cannot turn a whole CBB off)
- **CBBs:** Fully enable selected CBB, leaving first compute and module on the others

**Slice Configurations:**
- **Module-Based Selection:**
  - Selected module is kept alive on its corresponding compute, turning off all other computes on the CBB
  - For other CBBs, only first module is kept alive (cannot turn off a complete CBB)
- **Voltage/Frequency configurations** adapted to properly handle multiple CBBs

**Impact:** Enables full X4 chop testing capabilities for DMR validation.

---

### 7. ATE Configuration Support [DMR Only]

**Date:** February 2026
**Location:** `S2T/BASELINE_DMR/DebugFramework/ExecutionHandler/Configurations.py`

**New Feature:** ATE (Automated Test Equipment) configuration support with DFF data integration.

**Requirements:**
- Requires DFF data to be in CR (Code Repository) to work

**Mesh Mode:**
- Declares reference CBO to be used in voltage configuration
- Voltage/frequency settings based on DFF data

**Slice Mode:**
- Sets module based on selection
- MLC voltage adjusted based on selected frequency
- All data taken from DFF

**Data Sources:**
- ATE Safe Data taken from TP S604
- Voltage/Frequency subject to change based on Functional Content Addition

**Impact:** Enables ATE-mode testing with validated safe operating parameters.

---

### 8. DFF Data Collection Interface [DMR Only]

**Date:** February 2026
**Location:** `S2T/BASELINE_DMR/S2T/GetTesterRegs.py`, `DFFDataCollector.py`

**New Interface:** Comprehensive DFF (Design For Debug) data collection and management.

**GetTesterRegs API:**
```python
import users.THR.dmr_debug_utils.S2T.GetTesterRegs as gtc

# Dump uncore curves
gtc.dump_uncore_curves(<VID>, hot=True)

# Dump core curves (specific core or range)
gtc.dump_core_curves(<VID>, core=<physical_core>, hot=True)  # core range: [0,128]
```

**DFFDataCollector UI:**
```python
import users.THR.dmr_debug_utils.DFFDataCollector as dff

# Launch interactive UI
dff.UI()
```

**Features:**
- Interactive interface to generate DFF data for core/uncore
- Supports single VID or list of VIDs from `.txt` file
- Works offline with cached data
- DMR version uses cache: previously checked VIDs don't re-download

**Impact:** Streamlined DFF data collection with offline capabilities and caching.

---

### 9. CBB and Compute Configurations [DMR Only]

**Date:** February 2026
**Location:** `S2T/BASELINE_DMR/DebugFramework/`

**Updates:**
- Added CBB and compute configuration support in Debug Framework
- Updated `.nsh` bootscript files to properly calculate APIC IDs for X4 condition in slice mode
- Enhanced configuration validation for multi-CBB scenarios

**Impact:** Full integration of CBB-based architecture in Debug Framework.

---

## 🐛 BUG FIXES

### 1. Progress Calculation for Multi-Experiment Runs [Common]

**Files Modified:**
- `DebugFramework/UI/ControlPanel.py` (lines 4231, 4239)

**Issues Fixed:**
- Corrected calculation of current experiment contribution
- Fixed overall progress calculation across multiple experiments
- Improved progress bar accuracy

**Impact:** Users now see accurate progress when running multiple experiments in sequence or automation flows.

---

### 2. Status Update Synchronization [Common]

**Files Modified:**
- `DebugFramework/UI/StatusHandler.py` (multiple lines: 286, 355, 368, 455, 465, 534, 1394, 2002)

**Issues Fixed:**
- Added experiment statistics display
- Fixed missing handlers for FlowTestExecutor (line 120)
- Updated progress bar styles (lines 407, 688)
- Improved thread synchronization

**Impact:** Status panels now display real-time statistics and maintain consistent state across all execution modes.

---

### 3. Thread State Management [Common]

**Files Modified:**
- `DebugFramework/ExecutionHandler/utils/ThreadsHandler.py` (BASELINE_DMR)
- `DebugFramework/SystemDebug.py` (both repositories)

**New Features:**
- `acknowledged: bool` tracking for commands
- `processing_started: bool` state management
- Persistent command state for thread synchronization
- Persistent success state for critical commands

**Issues Fixed:**
- More lenient validation with timing flexibility (SystemDebug.py line 1914)
- Updated status manager context handling (line 2415)

**Impact:** Improved reliability in multi-threaded execution with better command tracking.

---

### 4. Process Panel Format Handling [Common]

**Files Modified:**
- `DebugFramework/UI/ProcessPanel.py` (line 1265)

**Issues Fixed:**
- New format handling for process output parsing

**Impact:** Better compatibility with different output formats.

---

### 5. Product-Specific Configuration Updates

#### GNR/CWF [GNR/CWF Only]
**File:** `S2T/product_specific/gnr/configs.py`
- Updated F3 values to 18 (Hex 0x12) - line 356
- Updated F4 values to 22 (Hex 0x16) - line 357

#### DMR [DMR Only]
Multiple updates with timestamps in 2025:
- `dpmChecks.py`: Updates 3/6/2025, 5/2/2025
- `SetTesterRegs.py`: Updates 27/6/2025, 3/6/2025
- `GetTesterCurves.py`: Updates 10/3/2025, 3/6/2025
- `mca_banks.py`: Last update 12/11/25
- `ErrorReportClass.py`: Last update 17/11/25

---

### 6. FuseOverride Core Values Delta_idx Fix [DMR Only]

**Location:** `S2T/BASELINE_DMR/S2T/SetTesterRegs.py`

**Issue Fixed:**
- FuseOverride and Core values were incorrectly modifying delta_idx fuses

**Solution:**
- **If fixed:** Set idx fuses to 0
- **If vbump:** No modification applied to idx fuses

**Impact:** Correct fuse configuration for fixed and vbump voltage scenarios.

---

### 7. Control Panel External Masks Bug [Common]

**Location:** `DebugFramework/UI/ControlPanel.py`

**Issue Fixed:**
- Bug when modifying experiments in Edit Window and applying External Masks
- Masks were being assigned as a string instead of a dictionary
- Caused Framework execution to fail

**Solution:**
- Proper dictionary assignment for external masks
- Validation added to ensure correct data type

**Impact:** External mask configurations now work correctly in experiment editing.

---

### 8. Boot Mode PYSV Console Breakpoint [Common]

**Location:** `DebugFramework/SystemDebug.py`

**Issue Fixed:**
- Boot Mode (PYSVConsole with breakpoint assigned) not properly assigning stop postcode
- Not logging on Boot console

**Solution:**
- Fixed postcode assignment logic
- Enabled boot console logging

**Impact:** PYSVConsole breakpoint mode now functions correctly.

---

### 9. S2T CLI Configuration Update [Common]

**Location:** `S2T/dpmChecks.py`

**Issue Fixed:**
- S2T CLI not updating configuration in mesh/slice modes when selecting ATE

**Solution:**
- Fixed configuration refresh logic for ATE mode

**Impact:** ATE mode selection now properly updates mesh/slice configurations.

---

### 10. Automation Designer Tab Bug [THR Tools]

**Location:** `DebugFramework/PPV/gui/`

**Issue Fixed:**
- Tab crash on experiment edit window after opening Experiment Report in same session

**Solution:**
- Fixed state management between report viewer and experiment editor

**Impact:** Stable tab navigation in Automation Designer.

---

### 11. Framework Reports DMR Support [THR Tools]

**Location:** `DebugFramework/PPV/parsers/`

**Enhancement:**
- Enabled DMR report parsing in Framework Report Builder
- DMR framework experiments can now be parsed with the tool

**Impact:** Unified reporting across all three products (GNR, CWF, DMR).

---

## 📈 IMPROVEMENTS

### 1. Enhanced Experiment Statistics Display [Common]

**Location:** `DebugFramework/UI/StatusHandler.py`, `ControlPanel.py`

- Real-time experiment counters (completed/total)
- Better progress visualization
- Improved status message formatting

---

### 2. Better Thread Synchronization [Common]

**Location:** `DebugFramework/ExecutionHandler/utils/ThreadsHandler.py`

- Persistent command state tracking
- Improved timing validation
- Better error handling

---

### 3. Product-Specific Folder Filtering [Common]

**Location:** `DEVTOOLS/deploy_universal.py`

- Automatic filtering based on selected product
- Prevents cross-contamination of product-specific code
- Improved deployment accuracy

---

## 📚 DOCUMENTATION UPDATES

All documentation updated to v1.7.1 (February 16-17, 2026):

### New Documentation:
1. **[MDT Tools and Fuse Dumps Quick Reference](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md)** ⭐
   - Version 1.7+ features guide
   - TOR dump generation workflows
   - Fuse/register dump procedures
   - Component availability checking

2. **[Credentials Setup Guide](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/installation/docs/CREDENTIALS_SETUP.md)** ⭐
   - AES-256 encryption details
   - Security best practices
   - Distribution guidelines

3. **[MaskEditor DMR Migration Guide](https://github.com/gaespino/Automation/blob/main/S2T/BASELINE_DMR/DebugFramework/MASKEDITOR_DMR_MIGRATION.md)** ⭐
   - Compute → CBB architecture migration
   - API changes and dictionary key updates
   - Grid layout comparison

4. **[MaskEditor Visual Comparison](https://github.com/gaespino/Automation/blob/main/S2T/BASELINE_DMR/DebugFramework/MASKEDITOR_VISUAL_COMPARISON.md)** ⭐
   - Side-by-side UI comparison
   - Layout differences explained

5. **[Debug Tools README](https://github.com/gaespino/Automation/blob/main/S2T/BASELINE_DMR/S2T/Tools/README_debugtools.md)** ⭐
   - MDT tools usage guide
   - Component reference

### Updated Documentation:
1. **[Main README.md](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/README.md)** - v1.7.1
   - Updated installation guide
   - Added installer quick start
   - New MDT tools reference

2. **[Installation Guide](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/INSTALLATION_GUIDE.md)** - v1.7.1
   - Encrypted credentials section
   - SSH/SCP transfer guide
   - Product-based defaults
   - Verbose logging instructions

3. **[Installation README](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/installation/README.md)** - v1.7.1
   - Package contents guide
   - Encrypted credentials setup
   - Quick start instructions

---

## 📦 DEPLOYMENT REPORTS

Recent deployments tracked in `DEVTOOLS/deployment_report_*.csv`:

### February 18, 2026
**Report:** `deployment_report_20260218_150631.csv`
**Product:** DMR
- `dpmChecks.py` (99.8% similarity - minimal changes)
- `Tools/registerdump.py` (89.9% similarity - minor changes)
- **NEW FILE:** `Tools/README_debugtools.md`
- **NEW FILE:** `test_curves.py`

### February 17, 2026
**Report:** `deployment_report_20260217_175121.csv`
**Product:** DMR
- `dpmChecks.py` (99.7%)
- `Tools/registerdump.py` (60.2% - significant changes)

### February 16, 2026
**Report:** `deployment_report_20260216_151910.csv`
**Product:** CWF
- `SetTesterRegs.py` → `CWFSetTesterRegs.py` (renamed)
- `CoreManipulation.py` → `CWFCoreManipulation.py` (renamed)
- `dpmChecks.py` → `dpmChecksCWF.py` (renamed with import replacements)
- **NEW FILE:** `Tools/registerdump.py`
- `managers/frequency_manager.py` (80.6% - minor changes)
- `managers/voltage_manager.py` (86.9% - minor changes)

### February 15, 2026
Multiple deployments with various configurations and file updates.

---

## 🔍 STRUCTURAL DIFFERENCES: BASELINE vs BASELINE_DMR

### Files in BASELINE Only (GNR/CWF Development):
- `DebugFramework/ExecutionHandler/Old_code.py`
- `DebugFramework/PPV/api/` (entire directory with dpmb.py)
- `DebugFramework/UI/MockControlPanel.py`
- `DebugFramework/UI/TestControlPanel.py`
- `DebugFramework/UI/GNRControlPanelConfig.json`
- `DebugFramework/UI/CWFControlPanelConfig.json`
- `DebugFramework/UI/GNRAutomationPanel.json`
- `DebugFramework/Automation_Flow/AutomationDesigner.py`
- Various test files and mock implementations

### Files in BASELINE_DMR Only (DMR Production):
- `DebugFramework/MASKEDITOR_DMR_MIGRATION.md` ⭐
- `DebugFramework/MASKEDITOR_VISUAL_COMPARISON.md` ⭐
- `S2T/Tools/debugtools.py` ⭐
- `S2T/Tools/README_debugtools.md` ⭐
- `S2T/test_curves.py` ⭐

### Common Components (Both Repositories):
- `DebugFramework/SystemDebug.py`
- `DebugFramework/FileHandler.py`
- `DebugFramework/TestFramework.py`
- `DebugFramework/ExecutionHandler/` (complete module)
- `DebugFramework/UI/` (core components)
- `DebugFramework/Storage_Handler/`
- `DebugFramework/PPV/` (parsers, gui, utils, Decoder)
- `S2T/CoreManipulation.py`
- `S2T/dpmChecks.py`
- `S2T/SetTesterRegs.py`
- `S2T/Logger/`
- `S2T/managers/`

---

## 📊 VERSION HISTORY

| Version | Date | Key Features |
|---------|------|--------------|
| **1.7.1** | Feb 19, 2026 | Automated installer, MDT tools, DMR MaskEditor migration, X4 chop support, ATE config, bug fixes |
| **2.0** | Jan 22, 2026 | DMR support, Automation Panel, Fuse Files, Control Panel improvements |

> **Note:** Version numbering realigned from v2.0 to v1.7.1 to match documentation versioning.

---

## ⚠️ KNOWN ISSUES

The following issues are known and will be addressed in future releases:

### 1. One Core Disable Configuration Warning [DMR]

**Issue:**
- When applying a 1 Core disable configuration, boot shows "not all fuses were applied"
- This is a nuisance warning only - functionality works correctly
- Script checks all disable fuses, and bootscript overrides modules that are off to 0

**Workaround:**
- Ignore the warning - configuration is applied correctly

**Planned Fix:**
- Update to only apply checks to corresponding fuses based on mask (future release)

---

### 2. "Disable 1 Core" Text Issue [DMR]

**Issue:**
- Text label "Test on Disable 1 Core" is misleading
- Actually performs "Enable 1 Core" - what is selected remains enabled
- This is a UI text issue only

**Workaround:**
- Understand that selection indicates what stays enabled, not disabled

**Planned Fix:**
- Update UI text to accurately reflect behavior (future release)

---

### 3. PYSVConsole BIOS Breakpoint Issue [Common]

**Issue:**
- PYSVConsole with BIOS breakpoint not performing expected result
- Does not stop at break as expected

**Workaround:**
- Use alternative breakpoint methods if critical

**Planned Fix:**
- Full breakpoint functionality repair (future release)

---

## 🚀 UPGRADE INSTRUCTIONS

### For All Products (GNR/CWF/DMR):

1. **Update Repository:**
   ```bash
   cd C:\Git\Automation\S2T\BASELINE        # For GNR/CWF
   cd C:\Git\Automation\S2T\BASELINE_DMR    # For DMR
   git pull origin main
   ```

2. **Run Installer (Recommended):**
   ```bash
   cd S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T\installation
   run_installer.bat
   ```

3. **Manual Setup (Alternative):**
   - Set up encrypted credentials using `credentials_manager.py`
   - Configure environment variables via `TeratermEnv.ps1`
   - Verify installation with documentation

4. **Verify Installation:**
   - Test Control Panel launch
   - Verify MDT tools access (DMR)
   - Check credential encryption status

---

## 📞 SUPPORT

For questions, issues, or feedback regarding this release:
- **Contact:** gaespino (GitHub: gaespino/Automation)
- **Documentation:** [Main Documentation](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/README.md)
- **Issues:** Report via email or GitHub issues

---

## 📝 NOTES

### For Developers:
- BASELINE_DMR excludes development test files (production-ready)
- BASELINE includes test mocks and development tools
- Product-specific code isolated in `S2T/product_specific/{gnr,cwf,dmr}/`
- Deployment tool v2.1 handles product filtering automatically

### Import Examples by Product:

**GNR:**
```python
import users.gaespino.DebugFramework.GNRSystemDebug as sd
sd.ControlPanel()
sd.AutomationPanel()
```

**CWF:**
```python
import users.gaespino.DebugFramework.CWFSystemDebug as sd
sd.ControlPanel()
sd.AutomationPanel()
```

**DMR:**
```python
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd
sd.ControlPanel()
sd.AutomationPanel()
```

### Security Notes:
- Encrypted credentials use AES-256-CBC encryption
- `credentials.enc` stored securely with machine-specific keys
- Never commit `credentials.enc` to version control
- Distribution: Share installer package, not credentials file

---

**Document Version:** 1.0
**Last Updated:** February 18, 2026
**Next Release Target:** TBD
