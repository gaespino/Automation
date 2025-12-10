# BASELINE External Dependencies Analysis

**Generated**: December 9, 2025  
**Source**: c:\Git\Automation\Automation\S2T\BASELINE

---

## 📦 External Python Packages (Non-Standard Library)

These are third-party packages that need to be installed via pip/conda:

### Data Processing & Analysis
- **pandas** - Data manipulation and analysis
- **numpy** - Numerical computing
- **openpyxl** - Excel file reading/writing (.xlsx)
- **xlwings** - Excel automation with Python

### Database
- **pymongo** - MongoDB driver

### GUI & Terminal
- **tkinter** - Built-in, but might need tk/tcl on some systems
- **colorama** - Cross-platform colored terminal text

### Utilities
- **tabulate** - Pretty-print tabular data
- **pytz** - Timezone calculations
- **psutil** - System and process utilities

---

## 🏢 Intel/Internal Packages

These appear to be Intel-specific or internal tools:

### IP/Silicon Tools
- **ipccli** - IP CLI tools
  - `ipccli.BitData`
  - `ipccli.stdiolog.log`
  - `ipccli.stdiolog.nolog`

### Silicon Verification Tools
- **namednodes** - Named node access
  - `namednodes.sv`
- **svtools** - Silicon validation tools
  - `svtools.common.baseaccess`

### Tool Extensions
- **toolext** - Tool extensions
  - `toolext.bootscript.boot`
  - `toolext.bootscript.toolbox.fuse_utility`

### Project Management
- **pm** - Project management utilities
  - `pm.pmutils.tools`

### XML Processing
- **lxml** - XML processing (external but often used in Intel tools)
  - `lxml.etree`

---

## 📋 Complete External Package List

### Required via pip/conda:
```
pandas
numpy
openpyxl
xlwings
pymongo
colorama
tabulate
pytz
psutil
lxml
```

### Intel Internal (Not in PyPI):
```
ipccli
namednodes
svtools
toolext
pm (project management tools)
registers (custom)
strategy (custom)
```

---

## 📁 Project-Specific Imports

These are internal modules within the BASELINE project:

### Core Framework
- `DebugFramework.*`
- `TestMocks`
- `TestFramework`
- `FileHandler`
- `MaskEditor`
- `SerialConnection`
- `SystemDebug`

### UI Components
- `UI.ControlPanel`
- `UI.ProcessPanel`
- `UI.StatusPanel`
- `UI.StatusHandler`
- `UI.Serial`
- `UI.Sweep`
- `UI.ExperimentsForm`
- `UI.AutomationPanel`

### Execution & Processing
- `ExecutionHandler.*`
  - `Configurations`
  - `Enums`
  - `Exceptions`
  - `StatusManager`
  - `utils.ThreadsHandler`
  - `utils.DebugLogger`
  - `utils.FrameworkUtils`
  - `utils.EmergencyCleanup`

### Automation
- `Automation_Flow.*`
  - `AutomationBuilder`
  - `AutomationFlows`
  - `AutomationTracker`
  - `AutomationHandler`

### PPV (Product Performance Validation)
- `PPV.parsers.MCAparser`
- `PPV.utils.PPVReportMerger`
- `PPV.gui.*`

### S2T (System to Tester)
- `S2T.ConfigsLoader`
- `S2T.managers.frequency_manager`
- `S2T.managers.voltage_manager`
- `S2T.UI.System2TesterUI`
- `S2T.CoreManipulation`
- `S2T.dpmChecks`

### Storage & Database
- `Storage_Handler.*`
  - `DBClient`
  - `DBHandler`
  - `DBUserInterface`
  - `ReportUtils`

### Interfaces
- `Interfaces.IFramework`

### Other Components
- `ConfigsLoader`
- `Logger.ErrorReportClass`
- `GetTesterCurves`
- `Decoder.decoder_dmr`

---

## 🔍 Import Patterns Analysis

### Most Common External Packages:
1. **pandas** - Used extensively for data manipulation
2. **openpyxl** - Excel file operations
3. **tkinter** - GUI components
4. **colorama** - Terminal coloring

### Intel-Specific Tools:
1. **ipccli** - IP command-line interface
2. **namednodes** - Silicon node access
3. **svtools** - Silicon validation
4. **toolext** - Boot scripts and utilities

### Standard Library (Most Used):
- `sys`, `os` - System operations
- `json` - JSON handling
- `datetime`, `time` - Time operations
- `threading`, `multiprocessing` - Concurrency
- `queue` - Thread-safe queues
- `dataclasses` - Data structures
- `typing` - Type hints
- `pathlib` - Path operations
- `re` - Regular expressions

---

## 📦 Suggested requirements.txt

For external packages only:

```txt
# Data Processing
pandas>=1.3.0
numpy>=1.21.0

# Excel Operations
openpyxl>=3.0.0
xlwings>=0.24.0

# Database
pymongo>=3.12.0

# Terminal/CLI
colorama>=0.4.4

# Utilities
tabulate>=0.8.9
pytz>=2021.1
psutil>=5.8.0

# XML Processing
lxml>=4.6.3
```

---

## 🚨 Intel Internal Dependencies

These must be available in your Intel environment:
- **ipccli** - Check Intel tool installation
- **namednodes** - Silicon validation toolkit
- **svtools** - Part of silicon tools suite
- **toolext** - Tool extensions framework
- **pm.pmutils** - Project management utilities

These are typically pre-installed on Intel development systems or available via internal package managers.

---

## 💡 Recommendations

### For Development:
1. Create a `requirements.txt` with the external packages listed above
2. Document Intel-specific tool requirements separately
3. Add version pinning for stability

### For Deployment:
1. Verify Intel tools are available in target environment
2. Install external packages: `pip install -r requirements.txt`
3. Test imports before deploying code

### For New Users:
1. Install external packages first
2. Verify Intel tool access
3. Run import test script to validate environment

---

## 🧪 Quick Import Test Script

```python
# test_imports.py
def test_external_imports():
    """Test all external package imports"""
    errors = []
    
    # External packages
    try:
        import pandas
        print("✓ pandas")
    except ImportError as e:
        errors.append(f"✗ pandas: {e}")
    
    try:
        import numpy
        print("✓ numpy")
    except ImportError as e:
        errors.append(f"✗ numpy: {e}")
    
    try:
        import openpyxl
        print("✓ openpyxl")
    except ImportError as e:
        errors.append(f"✗ openpyxl: {e}")
    
    try:
        import xlwings
        print("✓ xlwings")
    except ImportError as e:
        errors.append(f"✗ xlwings: {e}")
    
    try:
        import pymongo
        print("✓ pymongo")
    except ImportError as e:
        errors.append(f"✗ pymongo: {e}")
    
    try:
        import colorama
        print("✓ colorama")
    except ImportError as e:
        errors.append(f"✗ colorama: {e}")
    
    try:
        import tabulate
        print("✓ tabulate")
    except ImportError as e:
        errors.append(f"✗ tabulate: {e}")
    
    try:
        import pytz
        print("✓ pytz")
    except ImportError as e:
        errors.append(f"✗ pytz: {e}")
    
    try:
        import psutil
        print("✓ psutil")
    except ImportError as e:
        errors.append(f"✗ psutil: {e}")
    
    try:
        import lxml
        print("✓ lxml")
    except ImportError as e:
        errors.append(f"✗ lxml: {e}")
    
    # Intel-specific tools
    print("\nIntel-specific tools:")
    try:
        import ipccli
        print("✓ ipccli")
    except ImportError as e:
        errors.append(f"✗ ipccli: {e}")
    
    try:
        import namednodes
        print("✓ namednodes")
    except ImportError as e:
        errors.append(f"✗ namednodes: {e}")
    
    try:
        import svtools
        print("✓ svtools")
    except ImportError as e:
        errors.append(f"✗ svtools: {e}")
    
    if errors:
        print("\n❌ Errors found:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True

if __name__ == "__main__":
    test_external_imports()
```

---

## 📊 Summary Statistics

- **Total unique import statements**: 216
- **External packages (pip)**: 10
- **Intel internal tools**: ~5-7
- **Standard library modules**: ~40+
- **Project-specific modules**: 50+

---

**Note**: This analysis is based on import statements found in Python files. Actual runtime dependencies may vary based on execution paths and optional features.
