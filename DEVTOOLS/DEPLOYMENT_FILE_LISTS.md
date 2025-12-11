# Production Deployment File Lists

## Quick Reference: What to Deploy to Production

---

## DebugFramework Module

### ✅ INCLUDE in Production

#### Core Framework Files
- `__init__.py`
- `SystemDebug.py` - Main framework implementation
- `TestFramework.py` - Test execution framework
- `FileHandler.py` - File operations
- `SerialConnection.py` - Hardware serial communication
- `MaskEditor.py` - Mask editing utilities
- `Misc.py` - Miscellaneous utilities

#### ExecutionHandler/ (Complete Directory)
- `Configurations.py`
- `Enums.py`
- `Exceptions.py`
- `StatusManager.py`
- `utils/DebugLogger.py`
- `utils/EmergencyCleanup.py`
- `utils/FrameworkManager.py`
- `utils/FrameworkUtils.py`
- `utils/misc_utils.py`
- `utils/PanelManager.py`
- `utils/ReportGenerator.py`
- `utils/ThreadsHandler.py`
- `utils/ThreadsManager.py`

#### Interfaces/
- `IFramework.py`

#### Storage_Handler/
- `__init__.py`
- `DBClient.py`
- `DBHandler.py`
- `DBUserInterface.py`
- `MongoDBCredentials.py`
- `ReportUtils.py`

#### Automation_Flow/
- `__init__.py`
- `AutomationBuilder.py`
- `AutomationDesigner.py`
- `AutomationFlows.py`
- `AutomationHandler.py`
- `AutomationTracker.py`
- `TestFlow.py`
- `TestFlow1.py`
- `example.ini`
- `Flows.json`

#### UI/
- `__init__.py`
- `AutomationPanel.py`
- `ControlPanel.py`
- `ExperimentsForm.py`
- `ProcessPanel.py`
- `Serial.py`
- `StatusHandler.py`
- `StatusPanel.py`
- `Sweep.py`
- `CWFControlPanelConfig.json`
- `GNRControlPanelConfig.json`
- `GNRAutomationPanel.json`
- `ProcessHandler/` (complete directory)

#### PPV/ (Integration Components)
- `__init__.py`
- `run.py`
- `api/` (complete directory)
- `configs/` (all config files)
- `Decoder/` (complete directory)
- `gui/` (complete directory)
- `parsers/` (complete directory)
- `utils/` (complete directory)

#### Shmoos/
- `RVPShmooConfig.json`

#### TTL/ (Complete Directory)
- `Boot.ttl`
- `Commands_Linux.ttl`
- `Commands_slice.ttl`
- `Commands.ttl`
- `Connect.ttl`
- `Disconnect.ttl`
- `LinuxContent.ttl`
- `MeshContent.ttl`
- `SliceContent.ttl`
- `StartLog.ttl`
- `StopLog.ttl`

#### EFI/ (Complete Directory)
- `__init__.py`
- `apic_cdie0.nsh`
- `apic_cdie1.nsh`
- `apic_cdie2.nsh`
- `dbmvars.nsh`
- `Filecopy.py`
- `initdbm.nsh`
- `meshtest.nsh`
- `patternfinder.py`
- `slicetest.nsh`
- `slicevars.nsh`
- `TeratermEnv.ps1`

### ❌ EXCLUDE from Production

#### Test Files
- ❌ `TestRun.py` - Test launcher (development only)
- ❌ `TestMocks.py` - Mock implementations for testing
- ❌ `HardwareMocks.py` - Hardware simulation mocks
- ❌ `S2TMocks.py` - S2T mock implementations
- ❌ `S2TTestFramework.py` - Test framework utilities
- ❌ `UI/MockControlPanel.py` - Mock UI for testing
- ❌ `UI/TestControlPanel.py` - Test control panel
- ❌ `UI/test_config.py` - Test configuration

#### Development Files
- ❌ `ExecutionHandler/Old_code.py` - Deprecated code
- ❌ `Automation_Flow/dummy_structure.json` - Development dummy data
- ❌ `Automation_Flow/notes.txt` - Developer notes
- ❌ `Automation_Flow/old_interface.py` - Old implementation
- ❌ `Automation_Flow/reference_code_old.py` - Reference/backup code
- ❌ `UI/old_windows/` - Old UI implementations
- ❌ `UI/README_TEST.md` - Test documentation

#### Cache and Build Artifacts
- ❌ `**/__pycache__/`
- ❌ `**/*.pyc`
- ❌ `**/.pytest_cache/`

---

## S2T Module

### ✅ INCLUDE in Production

#### Core S2T Files
- `__init__.py`
- `ConfigsLoader.py` - Configuration management
- `CoreManipulation.py` - Core manipulation operations
- `DffDataCollector.py` - DFF data collection
- `dpmChecks.py` - DPM validation checks
- `GetTesterCurves.py` - Tester curve retrieval
- `SetTesterRegs.py` - Tester register configuration

#### managers/
- (Complete directory with all files)

#### Logger/
- (Complete directory with all files)

#### Tools/
- (Complete directory with all files)

#### Fuse/
- (Complete directory with all files)

#### UI/
- (Complete directory, excluding test files)

#### EFI Tools/
- (Complete directory with all files)

#### product_specific/ ⚠️ PRODUCT-SPECIFIC DEPLOYMENT
**IMPORTANT**: Deploy ONLY the target product folder
- For GNR deployment: `product_specific/GNR/` only
- For CWF deployment: `product_specific/CWF/` only
- For DMR deployment: `product_specific/DMR/` only

### ❌ EXCLUDE from Production

#### Test Files
- ❌ `**/test_*.py` - All test files
- ❌ `**/*_test.py` - All test files

#### Non-Target Product Folders
- ❌ `product_specific/GNR/` (if deploying CWF or DMR)
- ❌ `product_specific/CWF/` (if deploying GNR or DMR)
- ❌ `product_specific/DMR/` (if deploying GNR or CWF)

#### Cache Files
- ❌ `**/__pycache__/`
- ❌ `**/*.pyc`

---

## PPV Module

### ✅ INCLUDE in Production

#### Core PPV Files
- `__init__.py`
- `run.py` - Main entry point
- `requirements.txt` - Dependencies
- `README.md` - Documentation

#### api/
- `__init__.py`
- `dpmb.py`
- (All other API files)

#### Decoder/
- `__init__.py`
- `decoder_dmr.py`
- `decoder.py`
- `dragon_bucketing.py`
- `faildetection.py`
- `TransformJson.py`
- `CWF/` (complete directory)
- `DMR/` (complete directory)
- `GNR/` (complete directory)

#### gui/
- `__init__.py`
- `AutomationDesigner.py`
- `ExperimentBuilder.py`
- `PPVDataChecks.py`
- `PPVFileHandler.py`
- `PPVFrameworkReport.py`
- `PPVLoopChecks.py`
- `PPVTools.py`

#### parsers/
- `__init__.py`
- `FrameworkAnalyzer.py`
- (All parser files)

#### utils/
- (Complete directory with all utility files)

#### configs/
- `CWFControlPanelConfig.json`
- `DMRControlPanelConfig.json`
- `GNRControlPanelConfig.json`
- `README.md`

### ❌ EXCLUDE from Production

#### Backup Files
- ❌ `MCAparser_bkup.py` - Backup/legacy file

#### Installation Scripts
- ❌ `install_dependencies.bat` - Development setup
- ❌ `install_dependencies.py` - Development setup
- ❌ `process.ps1` - Development PowerShell script

#### Debug Scripts
- ❌ `DebugScripts/` (complete directory)
  - ❌ `add_aguila_user.ps1`
  - ❌ `LinuxContentLoops.sh`

#### Development Directories
- ❌ `.vscode/` - VS Code settings

#### Cache Files
- ❌ `**/__pycache__/`
- ❌ `**/*.pyc`

---

## Deployment Summary by File Count

### DebugFramework
- **Include**: ~80+ production files
- **Exclude**: ~15 test/development files
- **Key Exclusions**: All *Mock*.py, TestRun.py, old/deprecated code

### S2T
- **Include**: ~50+ production files (+ one product folder)
- **Exclude**: Test files + 2 non-target product folders
- **Key Exclusions**: test_*.py pattern, non-target product_specific folders

### PPV
- **Include**: ~40+ production files
- **Exclude**: ~5 development files + DebugScripts directory
- **Key Exclusions**: Backup files, installation scripts, debug scripts

---

## Validation Checklist

After deployment, verify:

### DebugFramework
- [ ] No TestRun.py in deployment
- [ ] No files containing "Mock" in name
- [ ] No test_*.py files
- [ ] No __pycache__ directories
- [ ] SystemDebug.py is present
- [ ] All UI components present (except test/mock files)
- [ ] TTL and EFI directories complete

### S2T
- [ ] Only ONE product_specific folder present (GNR OR CWF OR DMR)
- [ ] No test_*.py files
- [ ] Core files present (dpmChecks.py, CoreManipulation.py, etc.)
- [ ] No __pycache__ directories

### PPV
- [ ] No MCAparser_bkup.py
- [ ] No install_dependencies.* files
- [ ] No DebugScripts directory
- [ ] All three config files present (GNR, CWF, DMR)
- [ ] run.py is present
- [ ] Decoder has all three product subdirectories (CWF, DMR, GNR)

---

## File Counts Reference

Based on the BASELINE structure:

```
DebugFramework/
├── Core files: 7 files
├── ExecutionHandler/: 13+ files
├── Interfaces/: 1 file
├── Storage_Handler/: 6 files
├── Automation_Flow/: 8 production files (exclude 4 dev files)
├── UI/: 12 production files (exclude 3 test files)
├── PPV/: Complete integration
├── Shmoos/: 1 file
├── TTL/: 11 files
└── EFI/: 12 files

EXCLUDE: 15+ development/test files

S2T/
├── Core files: 7 files
├── managers/: Complete
├── Logger/: Complete
├── Tools/: Complete
├── Fuse/: Complete
├── UI/: Complete (minus test files)
├── EFI Tools/: Complete
└── product_specific/: Deploy 1 of 3 folders only

EXCLUDE: test_*.py + 2 non-target product folders

PPV/
├── Core files: 4 files
├── api/: Complete
├── Decoder/: Complete with all 3 product subdirs
├── gui/: Complete
├── parsers/: Complete
├── utils/: Complete
└── configs/: 4 files

EXCLUDE: 5 development files + DebugScripts directory
```
