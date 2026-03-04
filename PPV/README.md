# PPV Tools - Post-Package Validation Automation Suite

## Overview

The PPV (Post-Package Validation) Tools suite provides comprehensive automation tools for silicon validation, test execution, data analysis, and reporting.

## Available Tools

### 🎯 PPV Tools Hub
**Launcher**: `python run.py`

Centralized hub for all PPV automation tools with modern GUI interface.

**Included Tools:**
1. **PTC Loop Parser** - Parse PTC experiment logs and generate DPMB reports
2. **PPV MCA Report** - Generate MCA reports from Bucketer or S2T Logger data
3. **DPMB Requests** - Interface for Bucketer data requests via DPMB API
4. **File Handler** - Merge and manage multiple data files
5. **Framework Report Builder** - Create reports from Debug Framework data
6. **Automation Flow Designer** - Visual flow design for test automation
7. **Experiment Builder** ⭐ NEW - Create JSON configs for Control Panel

### 🆕 Experiment Builder (NEW!)

**Launcher**: `python run_experiment_builder.py` or via PPV Tools Hub

Create and manage JSON configuration files for the Debug Framework Control Panel.

**Key Features:**
- Visual experiment editor with tabbed interface
- Import from Excel (.xlsx) and JSON
- Export Control Panel-ready JSON files
- Real-time validation
- Experiment management (add, delete, duplicate, search)
- JSON preview with clipboard copy

**Quick Start:**
```bash
# Launch from hub
python run.py

# Or standalone
python run_experiment_builder.py

# Generate Excel template
python gui/create_excel_template.py
```

**Documentation:**
- 📖 User Guide: `EXPERIMENT_BUILDER_USER_GUIDE.md`
- 📚 Full README: `gui/EXPERIMENT_BUILDER_README.md`
- ⚡ Quick Start: `gui/QUICK_START.md`
- 🔧 Technical: `gui/IMPLEMENTATION_SUMMARY.md`

## Installation

### Quick Install

**Windows (Automated):**
```batch
cd c:\Git\Automation\Automation\PPV
install_dependencies.bat
```

**Cross-Platform:**
```bash
cd c:\Git\Automation\Automation\PPV
python install_dependencies.py
```

**Manual Installation:**
```bash
pip install -r requirements.txt
```

### Required Dependencies

**External Packages:**
- pandas ≥1.3.0 - Data manipulation
- numpy ≥1.20.0 - Numerical computing
- openpyxl ≥3.0.0 - Excel file handling
- xlwings ≥0.24.0 - Excel automation
- colorama ≥0.4.4 - Terminal colors
- tabulate ≥0.8.9 - Table formatting

**Standard Library** (included with Python):
- tkinter, json, os, sys, re, datetime, and more

📖 **Full installation guide:** See `INSTALLATION.md` for detailed instructions, troubleshooting, and virtual environment setup

## Usage

### Launch PPV Tools Hub
```bash
cd c:\Git\Automation\Automation\PPV
python run.py
```

### Launch Individual Tools

**Experiment Builder (Standalone):**
```bash
python run_experiment_builder.py
```

**Test Verification:**
```bash
python test_experiment_builder.py
```

**Generate Excel Template:**
```bash
python gui/create_excel_template.py
```

## Project Structure

```
PPV/
├── run.py                                  - PPV Tools Hub launcher
├── run_experiment_builder.py              - Experiment Builder standalone
├── test_experiment_builder.py             - Verification tests
├── EXPERIMENT_BUILDER_USER_GUIDE.md       - User guide (NEW)
├── __init__.py
├── MCAparser_bkup.py
├── process.ps1
│
├── gui/                                    - GUI Applications
│   ├── PPVTools.py                        - PPV Tools Hub main
│   ├── ExperimentBuilder.py               - Experiment Builder (NEW)
│   ├── AutomationDesigner.py              - Flow designer
│   ├── PPVDataChecks.py                   - MCA report generator
│   ├── PPVFileHandler.py                  - File management
│   ├── PPVFrameworkReport.py              - Framework reports
│   ├── PPVLoopChecks.py                   - PTC parser
│   ├── create_excel_template.py           - Template generator (NEW)
│   ├── Experiment_Template_Sample.xlsx    - Sample template (NEW)
│   ├── EXPERIMENT_BUILDER_README.md       - Full documentation (NEW)
│   ├── QUICK_START.md                     - Quick reference (NEW)
│   ├── IMPLEMENTATION_SUMMARY.md          - Technical details (NEW)
│   └── __init__.py
│
├── api/                                    - API Integrations
│   ├── dpmb.py                            - DPMB API interface
│   └── __init__.py
│
├── parsers/                                - Data Parsers
│   ├── FrameworkAnalyzer.py               - Framework analysis
│   ├── Frameworkparser.py                 - Framework parsing
│   ├── MCAparser.py                       - MCA parsing
│   ├── OverviewAnalyzer.py                - Overview analysis
│   ├── PPVLoopsParser.py                  - Loops parsing
│   └── MCChecker/                         - MC checking tools
│
├── utils/                                  - Utilities
│   ├── aqua_report.py                     - AQUA reporting
│   ├── ExcelReportBuilder.py              - Excel report generation
│   ├── folder_list.py                     - Folder utilities
│   ├── FrameworkFileFix.py                - Framework file fixes
│   └── PPVReportMerger.py                 - Report merging
│
├── Decoder/                                - Data Decoders
│   ├── decoder.py                         - Main decoder
│   ├── decoder_dmr.py                     - DMR decoder
│   ├── dragon_bucketing.py                - Dragon bucketing
│   ├── faildetection.py                   - Failure detection
│   ├── TransformJson.py                   - JSON transformation
│   ├── CWF/                               - CWF parameters
│   ├── DMR/                               - DMR parameters
│   └── GNR/                               - GNR parameters
│
└── DebugScripts/                          - Debug Utilities
    ├── add_aguila_user.ps1
    └── LinuxContentLoops.sh
```

## Integration with Debug Framework

The **Experiment Builder** generates JSON files that are directly compatible with the Debug Framework Control Panel:

**Workflow:**
1. Create experiments in Experiment Builder
2. Export to JSON file
3. Open Debug Framework Control Panel
4. Load the JSON file
5. Execute experiments

**Control Panel Location:**
- `S2T\BASELINE\DebugFramework\UI\ControlPanel.py`
- `S2T\BASELINE_DMR\DebugFramework\UI\ControlPanel.py`

## New Features (December 2024)

### ✨ Experiment Builder

Complete GUI tool for creating Control Panel configurations:

**Features:**
- 6 tabbed interface (Basic, Test Config, Voltage/Freq, Content, Advanced, JSON Preview)
- 50+ configurable fields
- Import from Excel/JSON
- Export to Control Panel-ready JSON
- Real-time validation
- Experiment management
- Search and filter
- JSON preview and clipboard copy

**Files Added:**
- `gui/ExperimentBuilder.py` - Main application (1,200+ lines)
- `run_experiment_builder.py` - Standalone launcher
- `test_experiment_builder.py` - Verification tests
- `gui/create_excel_template.py` - Template generator
- Complete documentation suite

**Integration:**
- Added to PPV Tools Hub (orange card, row 3)
- Standalone operation supported
- 100% Control Panel compatibility

## New Features (January 2026)

### 📥 PPV Folder Download

Added download functionality to Framework Report Builder for copying PPV folders from network to local storage.

**Features:**
- Download PPV folders from network server to local disk
- Progress indication during download
- Automatic fallback to network path if local not available
- Overwrite protection with user confirmation
- Asynchronous download to keep UI responsive
- Improved performance for large datasets

**Benefits:**
- Faster access to frequently used PPV data
- Reduced network dependency during analysis
- Better performance with large experiment datasets
- Seamless integration with existing workflow

**Usage:**
1. Launch Framework Report Builder from PPV Tools Hub
2. Select Product and Visual ID
3. Click "Browse" next to "Local PPV Folder" to select local storage location
4. Click "📥 Download PPV Folder" button
5. Wait for download to complete
6. Use "Parse Data" as normal - tool will automatically use local copy

**Technical Details:**
- Network source: `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\DebugFramework`
- Local path structure: `<local_base>/<product>/<visual_id>`
- Automatic path resolution in `parse_experiments()` and `create_report()`

## Documentation

### General
- This README - Overview and structure
- Tool-specific READMEs in subdirectories

### MCA Analysis
- **Developer Guide**: `analysis/MCA_ANALYSIS_README.md` — comprehensive reference for the MCA Analysis pipeline, per-product config files, priority rules system, and how to onboard new products (DMR) or add new IP types

### Experiment Builder
- **User Guide**: `EXPERIMENT_BUILDER_USER_GUIDE.md` - Start here!
- **Full README**: `gui/EXPERIMENT_BUILDER_README.md` - Complete manual
- **Quick Start**: `gui/QUICK_START.md` - Fast reference
- **Technical**: `gui/IMPLEMENTATION_SUMMARY.md` - Implementation details

### Examples
- Excel template: `gui/Experiment_Template_Sample.xlsx`
- Sample experiments included in template

## Testing

**Verify Experiment Builder:**
```bash
python test_experiment_builder.py
```

Expected: **5/5 tests passed** ✓

**Tests Include:**
1. Module import
2. Template loading
3. Default experiment creation
4. Excel template existence
5. Documentation completeness

## Support

### For Experiment Builder Issues:
1. Check validation report (click "Validate All")
2. Review documentation in `gui/`
3. Run verification tests
4. Check Excel template format
5. Contact automation team

### For Other PPV Tools:
- Check tool-specific documentation
- Review parser/decoder documentation
- Contact PPV team

## Version History

### December 2024 - Experiment Builder Release
- ✅ New Experiment Builder GUI tool
- ✅ Excel-to-JSON conversion
- ✅ Control Panel integration
- ✅ Complete documentation suite
- ✅ Template generation utility
- ✅ Verification test suite

## Contributing

When adding new tools or features:
1. Follow existing code structure
2. Add to PPV Tools Hub if GUI-based
3. Include documentation
4. Add verification tests
5. Update this README

## License

Internal Intel tool - For authorized use only.

---

**PPV Tools** - Comprehensive automation for silicon validation and testing.

*For questions or support, contact the automation team.*
