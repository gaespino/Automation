# PPV Tools - Reorganized Structure

## Overview
The PPV Tools package has been reorganized into a modular structure for better maintainability and clarity.

## New Folder Structure

```
PPV/
├── run_ppv_tools.py          # Main entry point - Run this to start the application
├── __init__.py               # Package initialization
│
├── gui/                      # GUI modules
│   ├── __init__.py
│   ├── PPVTools.py          # Main hub interface (Entry point)
│   ├── PPVLoopChecks.py     # PTC Loop Parser GUI
│   ├── PPVDataChecks.py     # PPV MCA Report GUI
│   ├── PPVFileHandler.py    # File Handler GUI
│   └── PPVFrameworkReport.py # Framework Report Builder GUI
│
├── parsers/                  # Data parsing modules
│   ├── __init__.py
│   ├── PPVLoopsParser.py    # PTC loop data parser
│   ├── MCAparser.py         # MCA data parser
│   ├── Frameworkparser.py   # Framework data parser
│   ├── FrameworkAnalyzer.py # Framework analysis utilities
│   └── OverviewAnalyzer.py  # Overview generation
│
├── utils/                    # Utility modules
│   ├── __init__.py
│   ├── PPVReportMerger.py   # Excel report merging utilities
│   ├── ExcelReportBuilder.py # Excel report generation
│   ├── FrameworkFileFix.py  # Framework file fixes
│   ├── folder_list.py       # Folder operations
│   └── aqua_report.py       # Aqua report utilities
│
├── api/                      # API integration modules
│   ├── __init__.py
│   └── dpmb.py              # DPMB API interface
│
├── Decoder/                  # MCA decoder modules (existing)
│   └── ...
│
├── MCChecker/                # MCA checker tools (existing)
│   └── ...
│
└── DebugScripts/             # Debug and utility scripts (existing)
    └── ...
```

## How to Run

### Option 1: Using the Entry Point Script (Recommended)
```powershell
cd c:\Git\Automation\Automation\PPV
python run_ppv_tools.py
```

### Option 2: Direct Module Import
```python
from PPV.gui.PPVTools import Tools, display_banner
import tkinter as tk

display_banner()
root = tk.Tk()
app = Tools(root)
root.mainloop()
```

## Module Organization

### GUI Modules (`gui/`)
All graphical user interface components:
- **PPVTools.py**: Main hub interface with color-coded tool cards
- **PPVLoopChecks.py**: PTC Loop Parser interface (Blue #3498db)
- **PPVDataChecks.py**: PPV MCA Report Builder interface (Red #e74c3c)
- **PPVFileHandler.py**: File merge/append operations interface (Orange #f39c12)
- **PPVFrameworkReport.py**: Framework Report Builder interface (Teal #1abc9c)

### Parser Modules (`parsers/`)
Data parsing and analysis logic:
- **PPVLoopsParser.py**: Parses PTC experiment loop data
- **MCAparser.py**: Parses Machine Check Architecture data
- **Frameworkparser.py**: Parses Debug Framework experiment data
- **FrameworkAnalyzer.py**: Analyzes framework data patterns
- **OverviewAnalyzer.py**: Generates overview summaries

### Utility Modules (`utils/`)
Helper functions and utilities:
- **PPVReportMerger.py**: Merges multiple Excel reports
- **ExcelReportBuilder.py**: Builds formatted Excel reports
- **FrameworkFileFix.py**: Fixes framework file issues
- **folder_list.py**: Folder listing and operations
- **aqua_report.py**: Aqua-specific report generation

### API Modules (`api/`)
External service integrations:
- **dpmb.py**: DPMB Bucketer API interface (Purple #9b59b6)

## Import Updates

All import statements have been updated to use relative imports based on the new structure:

```python
# GUI imports from other GUI modules
from .PPVLoopChecks import PTCReportGUI

# GUI imports from parsers
from ..parsers.MCAparser import ppv_report

# GUI imports from utils
from ..utils import PPVReportMerger

# GUI imports from api
from ..api.dpmb import dpmbGUI

# Parser imports from Decoder
from ..Decoder import decoder
```

## Benefits of New Structure

1. **Clear Separation of Concerns**: GUI, parsing, utilities, and API code are separated
2. **Better Maintainability**: Easier to locate and modify specific functionality
3. **Improved Modularity**: Components can be reused independently
4. **Cleaner Namespace**: Reduced risk of naming conflicts
5. **Professional Structure**: Follows Python package best practices

## Color Coding

Each tool window has a colored header bar matching its card in the main hub:
- **Blue (#3498db)**: PTC Loop Parser
- **Red (#e74c3c)**: PPV MCA Report
- **Purple (#9b59b6)**: DPMB Requests
- **Orange (#f39c12)**: File Handler
- **Teal (#1abc9c)**: Framework Report Builder

## Version
**Version 2.0.0** - Reorganized structure with improved modularity and usability
