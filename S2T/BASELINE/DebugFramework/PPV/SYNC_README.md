# PPV Files Sync to S2T DebugFramework

## Overview
The necessary PPV files have been synchronized from the main PPV folder to the S2T\BASELINE and S2T\BASELINE_DMR\DebugFramework\PPV folders.

## Files Copied

### Core Python Files
1. **MCAparser.py** - MCA data parser with decoder support
2. **PPVReportMerger.py** - Excel report merging utilities  
3. **PPVDataChecks.py** - PPV MCA Report GUI (optional, for standalone use)

### Framework Analysis Files
4. **Frameworkparser.py** - Debug Framework parser with comprehensive analysis
5. **FrameworkAnalyzer.py** - Experiment summary and characterization analysis
6. **OverviewAnalyzer.py** - Stakeholder-friendly unit overview generator
7. **ExcelReportBuilder.py** - Flexible Excel report builder with styling
8. **PPVFrameworkReport.py** - Framework Report Builder GUI

### Supporting Folders
1. **Decoder/** - MCA decoder modules with product-specific parameter files
   - decoder.py, decoder_dmr.py, dragon_bucketing.py, faildetection.py
   - Product folders: GNR/, CWF/, DMR/ with JSON parameter files
   
2. **DebugScripts/** - Utility scripts
   - add_aguila_user.ps1
   - LinuxContentLoops.sh

3. **MCChecker/** - MCA checker tools and templates
   - Excel templates for different products
   - Product-specific folders: GNR/, CWF/, DMR/

## Import Structure Updates

### In S2T\BASELINE\DebugFramework\PPV\

#### MCAparser.py
```python
# Import decoder module
try:
    from .Decoder import decoder as mcparse
except ImportError:
    try:
        from Decoder import decoder as mcparse
    except ImportError:
        sys.path.append(os.path.abspath(os.path.dirname(__file__)))
        from Decoder import decoder as mcparse
```

#### PPVReportMerger.py
```python
# Import MCAparser
try:
    from . import MCAparser as mca
except ImportError:
    import MCAparser as mca
```

#### PPVDataChecks.py
```python
try:
    from .MCAparser import ppv_report as mcap
except ImportError:
    import MCAparser
    ppv_report = MCAparser.ppv_report
```

### In S2T\BASELINE\DebugFramework\FileHandler.py

The FileHandler.py already uses the correct imports:
```python
import PPV.MCAparser as parser
import PPV.PPVReportMerger as merger
```

This allows FileHandler to access the PPV modules as a package.

## Locations

### BASELINE
```
S2T\BASELINE\DebugFramework\
├── FileHandler.py (imports PPV modules)
└── PPV\
    ├── __init__.py
    ├── MCAparser.py
    ├── PPVReportMerger.py
    ├── PPVDataChecks.py
    ├── Decoder\
    ├── DebugScripts\
    └── MCChecker\
```

### BASELINE_DMR
```
S2T\BASELINE_DMR\DebugFramework\
├── FileHandler.py (imports PPV modules)
└── PPV\
    ├── __init__.py
    ├── MCAparser.py
    ├── PPVReportMerger.py
    ├── PPVDataChecks.py
    ├── Decoder\
    ├── DebugScripts\
    └── MCChecker\
```

## Usage

### From FileHandler.py
```python
import PPV.MCAparser as parser
import PPV.PPVReportMerger as merger

# Use parser
report = parser.ppv_report(name=name, week=week, ...)
report.run()

# Use merger
merger.merge_excel_files(input_folder, output_file, prefix='MCA_Report')
```

### Standalone PPVDataChecks GUI
```python
# Can be run directly from S2T\BASELINE\DebugFramework\PPV\
python PPVDataChecks.py
```

## Key Features

1. **Flexible Imports**: All modules support both package-style imports (relative) and direct imports (absolute)
2. **Decoder Support**: Full decoder functionality with product-specific parameters
3. **No Breaking Changes**: Existing FileHandler.py code continues to work without modification
4. **Synchronized**: Same codebase as main PPV folder ensures consistency

## Maintenance - SIMPLIFIED! ✅

**S2T now has the SAME structure as main PPV!**

To update files, just copy entire folders:

```powershell
$src = "c:\Git\Automation\Automation\PPV"

# Copy to BASELINE
$dest = "c:\Git\Automation\Automation\S2T\BASELINE\DebugFramework\PPV"
Copy-Item "$src\gui\*" "$dest\gui\" -Force
Copy-Item "$src\parsers\*" "$dest\parsers\" -Force
Copy-Item "$src\utils\*" "$dest\utils\" -Force
Copy-Item "$src\api\*" "$dest\api\" -Force
Copy-Item "$src\Decoder" "$dest\" -Recurse -Force
Copy-Item "$src\DebugScripts" "$dest\" -Recurse -Force
Copy-Item "$src\MCChecker" "$dest\" -Recurse -Force
Copy-Item "$src\__init__.py" "$dest\" -Force
Copy-Item "$src\run_ppv_tools.py" "$dest\" -Force

# Copy to BASELINE_DMR (same process)
$dest = "c:\Git\Automation\Automation\S2T\BASELINE_DMR\DebugFramework\PPV"
Copy-Item "$src\gui\*" "$dest\gui\" -Force
Copy-Item "$src\parsers\*" "$dest\parsers\" -Force
Copy-Item "$src\utils\*" "$dest\utils\" -Force
Copy-Item "$src\api\*" "$dest\api\" -Force
Copy-Item "$src\Decoder" "$dest\" -Recurse -Force
Copy-Item "$src\DebugScripts" "$dest\" -Recurse -Force
Copy-Item "$src\MCChecker" "$dest\" -Recurse -Force
Copy-Item "$src\__init__.py" "$dest\" -Force
Copy-Item "$src\run_ppv_tools.py" "$dest\" -Force
```

**No import changes needed** - imports already work with this structure!

## Version
Synced from PPV Tools v2.0.0 (reorganized structure) on November 21, 2025

## Complete File List

### Python Modules
- **MCAparser.py** - Machine Check Architecture parser
- **PPVReportMerger.py** - Excel report merging utilities
- **PPVDataChecks.py** - PPV MCA data validation GUI
- **Frameworkparser.py** - Debug Framework comprehensive parser
- **FrameworkAnalyzer.py** - Experiment analysis and characterization
- **OverviewAnalyzer.py** - Unit overview presentation generator
- **ExcelReportBuilder.py** - Excel report builder with styling
- **PPVFrameworkReport.py** - Framework Report Builder GUI

### Folders
- **Decoder/** - MCA decoder with product configs (GNR, CWF, DMR)
- **DebugScripts/** - PowerShell and shell utility scripts
- **MCChecker/** - Excel MCA checker templates
