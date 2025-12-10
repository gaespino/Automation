# BASELINE Import Analysis - Quick Summary

**Generated**: December 9, 2025  
**Total Files Analyzed**: 144 Python files  
**Total Unique Imports**: 343

---

## 📊 Summary Statistics

| Category | Packages | File References |
|----------|----------|-----------------|
| External (pip/conda) | 10 | 88 |
| Intel Internal | 8 | 41 |
| Standard Library | 40 | 473 |
| Project Modules | 18 | 59 |
| Relative Imports | 1 | 15 |
| Other | 39 | 118 |

---

## 📦 External Packages Usage

### Most Used External Packages

| Package | Files Using It | Key Modules |
|---------|----------------|-------------|
| **pandas** | 27 files | Data processing, parsers, analysis |
| **openpyxl** | 17 files | Excel operations, reports |
| **tabulate** | 17 files | Pretty tables, reporting |
| **colorama** | 11 files | Terminal colors, UI |
| **xlwings** | 3 files | Excel automation (PPV tools) |
| **numpy** | 3 files | Numerical analysis |
| **psutil** | 3 files | Process management |
| **pytz** | 3 files | Timezone handling |
| **pymongo** | 2 files | Database operations |
| **lxml** | 2 files | XML processing |

---

## 🏢 Intel-Specific Packages Usage

| Package | Files Using It | Primary Use |
|---------|----------------|-------------|
| **ipccli** | 13 files | IP command-line interface |
| **namednodes** | 14 files | Silicon node access |
| **toolext** | 7 files | Boot scripts, utilities |
| **svtools** | 2 files | Silicon validation tools |
| **pm** | 1 file | Project management tools |
| **configs** | 2 files | Configuration access |
| **registers** | 1 file | Register definitions |
| **strategy** | 1 file | Product strategy |

---

## 📚 Top Standard Library Modules

| Module | Files | Purpose |
|--------|-------|---------|
| os | 77 | File system operations |
| sys | 66 | System operations |
| time | 36 | Time operations |
| typing | 35 | Type hints |
| datetime | 33 | Date/time handling |
| json | 29 | JSON processing |
| threading | 22 | Multi-threading |
| dataclasses | 20 | Data structures |
| re | 16 | Regular expressions |
| enum | 14 | Enumerations |

---

## 🔧 Key Project Modules

| Module | Files | Description |
|--------|-------|-------------|
| DebugFramework | 11 | Core framework |
| UI | 7 | User interface components |
| ExecutionHandler | 7 | Test execution |
| FileHandler | 6 | File operations |
| ConfigsLoader | 6 | Configuration loading |
| S2T | 3 | System-to-Tester |
| TestMocks | 3 | Testing utilities |

---

## 🎯 Where External Packages Are Used

### pandas (27 files)
**Primary locations:**
- `DebugFramework/PPV/parsers/` - Data parsing
- `DebugFramework/PPV/Decoder/` - Data decoding
- `S2T/` - System-to-Tester operations
- `DebugFramework/FileHandler.py` - File operations

### openpyxl (17 files)
**Primary locations:**
- `DebugFramework/PPV/parsers/` - Excel parsing
- `DebugFramework/PPV/utils/` - Excel utilities
- `DebugFramework/UI/ExperimentsForm.py` - UI forms
- `S2T/Logger/` - Report generation

### colorama (11 files)
**Primary locations:**
- `DebugFramework/UI/` - UI components
- `DebugFramework/SystemDebug.py` - Debug output
- `S2T/CoreManipulation.py` - Core operations
- Product-specific functions (cwf, dmr, gnr)

### tabulate (17 files)
**Primary locations:**
- `DebugFramework/SystemDebug.py` - Debug tables
- `S2T/` - Various reporting tools
- `DebugFramework/PPV/` - Report generation

---

## 📍 Intel Tools Distribution

### ipccli (13 files)
**Used in:**
- `DebugFramework/S2TMocks.py`
- `DebugFramework/SystemDebug.py`
- `S2T/ConfigsLoader.py`
- `S2T/CoreManipulation.py`
- `S2T/Logger/` - Multiple files
- `S2T/SetTesterRegs.py`

### namednodes (14 files)
**Used in:**
- `DebugFramework/SystemDebug.py`
- `S2T/ConfigsLoader.py`
- `S2T/CoreManipulation.py`
- `S2T/Logger/` - Multiple files
- Product-specific functions

### toolext (7 files)
**Used in:**
- `DebugFramework/S2TMocks.py`
- `S2T/CoreManipulation.py`
- `S2T/Logger/` - Legacy report files
- `S2T/dpmChecks.py`

---

## 💡 Installation Requirements

### Required External Packages
```bash
pip install pandas numpy openpyxl xlwings pymongo colorama tabulate pytz psutil lxml
```

### Intel Internal Tools
These must be available in your Intel environment:
- ipccli
- namednodes
- svtools
- toolext
- pm.pmutils

---

## 📄 Detailed Reports Available

1. **BASELINE_IMPORTS_DETAILED.md** - Full detailed report
   - All imports with exact file locations and line numbers
   - Grouped by package
   - Complete usage patterns

2. **BASELINE_DEPENDENCIES.md** - Comprehensive guide
   - Package descriptions
   - Installation instructions
   - Test scripts

3. **test_dependencies.py** - Environment verification
   - Tests all package imports
   - Identifies missing packages
   - Shows version information

---

## 🚀 Quick Start

1. **Check your environment:**
   ```bash
   cd S2T/BASELINE
   python test_dependencies.py
   ```

2. **Install missing packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Intel tools access** - Contact IT if tools are missing

---

## 📞 Need More Info?

- **Full details**: See `BASELINE_IMPORTS_DETAILED.md` (591 lines)
- **Package info**: See `BASELINE_DEPENDENCIES.md`
- **Test environment**: Run `test_dependencies.py`
- **Generate fresh report**: Run `analyze_imports.py`

---

**Last Updated**: December 9, 2025
