# Debug Framework v2.01 / 2.1 (DMR) Release Email - February 19, 2026

---

**Subject:** Debug Framework v2.01 / 2.1 (DMR) Release - Automated Installer, MDT Tools & DMR Enhancements

---

Hi Team,

Debug Framework release **v2.01** (GNR/CWF) / **v2.1** (DMR) is ready and updated in all supported product repositories (**GNR / CWF / DMR**). This release introduces major improvements in installation automation, hardware debugging capabilities, and DMR-specific architecture enhancements. Please update your system repository to include the latest version.

---

## 🎯 HIGHLIGHTS OF THIS RELEASE

✅ **Faster Setup** - One-click installer reduces setup time from 30+ minutes to under 5 minutes
✅ **Enhanced Security** - AES-256 encrypted credentials eliminate password exposure
✅ **Better Hardware Debug** - MDT tools provide direct access to 41 hardware components
✅ **DMR Architecture Support** - Native CBB-based masking for Diamond Rapids
✅ **X4 Chop Testing** - Full 4-CBB testing capabilities for DMR validation
✅ **ATE Configuration** - Integrated DFF data support for automated test equipment
✅ **DFF Data Collection** - New offline-capable interface with intelligent caching
✅ **Fuse File Generators** - Multiple tools for easier creation of fuse files for debug
✅ **Improved Reliability** - Multiple bug fixes for progress tracking, thread management, and Control Panel
✅ **Comprehensive Documentation** - Five new guides covering installation, MDT tools, and DMR migration
✅ **THR Tools Updates** - DMR support in Framework Reports, Automation Designer fixes

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
   cd I:\ppv_transfer_data\SystemDebug\installation\
   run_installer.bat
   ```

3. **Verify Installation:**
   - Test Control Panel launch
   - Verify MDT tools access (DMR)
   - Check credential encryption status

---

## 🆕 NEW FEATURES

### **Automated GUI Installer with Encrypted Credentials** – All Products
- **One-click installation** via `run_installer.bat`
- **AES-256 encrypted credential storage** - No manual password entry required
- **Automatic environment setup** - TeraTerm paths, serial ports, SSH/SCP configuration
- **Product-based defaults** - Pre-configured for GNR, CWF, and DMR
- **Location:** `\\amr\ec\proj\mdl\cr\intel\ppv_transfer_data\SystemDebug\installation\`

**Quick Start:**
```bash frpm any RVP at CR site
cd I:\ppv_transfer_data\SystemDebug\installation\
run_installer.bat
```

### **MDT Tools Integration** – DMR
- Access to **41 debug hardware components** (CCF, cache, FIVR, pm, xbar, etc.)
- **TOR dump generation** from CCF for transaction analysis
- **Fuse/register dump** functionality for configuration export
- **Unified API** for hardware debugging

**New Functions:**
- `tor_dump()` - Generate Transaction Ordering Ring dumps
- `fuse_dump()` - Export complete register/fuse values
- `mdt_tools()` - Initialize and access debug components
- 'generate_fusefile()' - Generates a .fuse file from a provided array

**Usage Example:**
```python
import dpmChecks as dpm

# Initialize MDT tools
tools = dpm.mdt_tools()

# Generate TOR dump
dpm.tor_dump()

# Export fuse registers
dpm.fuse_dump()

# Generate fuse file from an array
dpm.generate_fusefile()
```

### **DMR MaskEditor Architecture Migration** – DMR Only
- **Complete redesign** for CBB (Compute Building Block) architecture
- **Changed from:** 3 Computes with 60-bit masks → **To:** 4 CBBs with 32-bit masks
- **New 8×4 grid layout** matching DMR tileview architecture
- **Simplified interface** - Column-first indexing (DCM0-3)
- Support for **chop detection (X1-X4)** and **variant detection (AP/SP)**

### **DMR Configuration Enhancements** – DMR Only
- Update to accept up to 4 CBBs
- Updated DFF Data collection script
- Added ATE Curves data
- ATE Mode can now be used for Frequency and Voltage

### **X4 Chop Support** – DMR Only ⭐ NEW
- **Full X4 chop testing** capabilities enabled for DMR
- **Mesh configurations:** Compute-based selection across all CBBs
- **Slice configurations:** Module-based selection with proper CBB handling
- **Voltage/Frequency:** Adapted to handle multiple CBBs correctly

### **ATE Configuration Support** – DMR Only ⭐ NEW
- Requires DFF data in CR to function
- **Mesh mode:** Reference CBO declaration for voltage configuration
- **Slice mode:** Module-based with MLC voltage adjustment
- ATE Safe Data from TP S604

### **DFF Data Collection Interface** – DMR Only ⭐ NEW
- New interactive UI for DFF data generation
- Supports single VID or list of VIDs from `.txt` file
- **Offline capable** with intelligent caching
- API functions: `dump_uncore_curves()`, `dump_core_curves()`

**Usage:**
```python
import users.THR.dmr_debug_utils.S2T.GetTesterRegs as gtc
gtc.dump_uncore_curves(<VID>, hot=True)
gtc.dump_core_curves(<VID>, core=<physical_core>, hot=True)

import users.THR.dmr_debug_utils.DFFDataCollector as dff
dff.UI()  # Launch interactive interface
```

---

## 🐛 UPDATES / FIXES

### **System 2 Tester** – DMR Only
- ✅ **X4 Chops fully operational** - Mesh and Slice modes support all 4 CBBs
- ✅ **FuseOverride delta_idx fix** - Corrected core value modifications (fixed sets idx to 0, vbump no modification)
- ✅ **ATE Configuration added** - Full integration with DFF data
- ✅ **DFF Data available** - GetTesterRegs and DFFDataCollector interfaces
- ✅ **Updated .nsh files** - Proper APIC ID calculation for X4 condition in slice mode

### **System 2 Tester** – All Products
- ✅ **S2T CLI configuration** - Fixed update issue in mesh/slice modes when selecting ATE

### **Debug Framework** – DMR Only
- ✅ **CBB and compute configurations** - Full integration in Debug Framework
- ✅ **Bootscript updates** - Enhanced APIC ID handling for X4

### **Debug Framework** – All Products
- ✅ **Control Panel External Masks bug** - Fixed dictionary assignment issue causing execution failures
- ✅ **Boot Mode PYSV Console** - Fixed breakpoint postcode assignment and logging

### **Status Update Synchronization** – All Products
- ✅ Added real-time experiment statistics display
- ✅ Fixed missing handlers for FlowTestExecutor
- ✅ Improved thread synchronization and state management
- ✅ Better status panel consistency

### **Thread State Management** – All Products
- ✅ New persistent command state tracking (`acknowledged`, `processing_started`)
- ✅ More lenient timing validation
- ✅ Improved reliability in multi-threaded execution

### **THR Tools** – All Products
- ✅ **Automation Designer** - Fixed tab crash after opening Experiment Report
- ✅ **Framework Report Builder** - Enabled DMR report parsing

### **Product-Specific Configuration Updates**
- **GNR/CWF:** Updated F3 and F4 frequency values
- **DMR:** Multiple stability and compatibility improvements

---

## ⚠️ KNOWN ISSUES

The following issues are known and will be addressed in future releases:

1. **One Core Disable Configuration Warning (DMR)** - Warning appears but configuration works correctly. Nuisance message only.
2. **"Disable 1 Core" Text Issue (DMR)** - Label is misleading; actually performs "Enable 1 Core". UI text will be updated.
3. **PYSVConsole BIOS Breakpoint (All)** - Breakpoint not stopping as expected. Workaround: use alternative methods.

---

## 📚 DOCUMENTATION

All documentation updated to **v1.7.1**:

| Documentation | Link |
|---------------|------|
| **Main README** | [README.md](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/README.md) |
| **Debug Framework & S2T** | [THR_DEBUG_FRAMEWORK_USER_MANUAL.md](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/THR_DEBUG_FRAMEWORK_USER_MANUAL.md) |
| **Installation Guide** ⭐ NEW | [INSTALLATION_GUIDE.md](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/INSTALLATION_GUIDE.md) |
| **MDT Tools Quick Reference** ⭐ NEW | [MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/MDT_TOOLS_AND_FUSE_DUMPS_QUICK_REFERENCE.md) |
| **Credentials Setup** ⭐ NEW | [CREDENTIALS_SETUP.md](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/installation/docs/CREDENTIALS_SETUP.md) |
| **MaskEditor DMR Migration** ⭐ NEW | [MASKEDITOR_DMR_MIGRATION.md](https://github.com/gaespino/Automation/blob/main/S2T/BASELINE_DMR/DebugFramework/MASKEDITOR_DMR_MIGRATION.md) |
| **THR Debug Tools** | [THR_DEBUG_TOOLS_USER_MANUAL.md](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/PPV/THR_DEBUG_TOOLS_USER_MANUAL.md) |

---


## 📋 PRODUCT IMPORT EXAMPLES

### GNR (Granite Rapids)
```python
import users.gaespino.DebugFramework.GNRSystemDebug as sd
sd.ControlPanel()
sd.AutomationPanel()
```

### CWF (Clearwater Forest)
```python
import users.gaespino.DebugFramework.CWFSystemDebug as sd
sd.ControlPanel()
sd.AutomationPanel()
```

### DMR (Diamond Rapids)
```python
import users.THR.dmr_debug_utilities.DebugFramework.SystemDebug as sd
sd.ControlPanel()
sd.AutomationPanel()
```

---

## 🔧 THR DEBUG TOOLS

The complete suite of debug tools is available for all three products:

| Tool | Description |
|------|-------------|
| **DPMB** | Query Intel's DPMB API for bucket data and offline analysis |
| **MCA Report** | Generate comprehensive MCA reports from Framework logs |
| **PTC Loop Parser** | Parse PTC loop data and generate Excel reports |
| **MCA Single Decoder** | Interactive decoder for MCA register values (CHA, LLC, CORE, MEMORY, IO) |
| **File Handler** | Merge or append multiple Excel report files |
| **Automation Flow Designer** | Visual designer for test automation sequences |
| **Experiment Builder** | Excel-like interface for JSON configuration files |
| **Framework Report Builder** | Generate experiment reports from execution logs (now with **DMR support**) |
| **Fuse File Generator** ⭐ NEW | Engineering tool to generate fuse files from offline fuse data |

**Recent Updates:**
- ✅ **Automation Designer** - Fixed tab crash issue after opening reports
- ✅ **Framework Reports** - Now supports DMR experiment parsing
- ✅ **Fuse File Generator** - NEW tool for easier fuse file creation

---

## 📞 SUPPORT

Any questions or issues with the update, feel free to contact me.

For detailed release notes and file-level changes, see:
`DEVTOOLS/deploys/RELEASE_v1.7.1_Feb2026.md`

---

**Version:** 1.7.1
**Release Date:** February 19, 2026
**Products:** GNR, CWF, DMR

---

Best regards,
Gabriel Espinoza B
