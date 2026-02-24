# Universal Deployment Tool

Deploy code from **BASELINE**, **BASELINE_DMR**, or **PPV** to product-specific locations with intelligent import replacement and selective deployment.

## 🚀 Quick Start

### Launch the Tool

**Option 1: Batch File (Windows)**
```batch
launch_deploy_universal.bat
```

**Option 2: Python Direct**
```bash
python deploy_universal.py
```

### Basic Workflow (Tab 1 — Deploy)

1. **Select Source**: Choose BASELINE, BASELINE_DMR, or PPV
2. **Select Deployment Type**: Choose S2T or DebugFramework (or PPV for PPV source)
3. **Select Product**: GNR, CWF, or DMR
4. **Select Target**: Click "Select Target..." and choose destination directory
5. **Load Import Replacements** (Optional): Load or generate a CSV with replacement rules
6. **Load File Rename CSV** (Optional): Load CSV to rename files during deployment
7. **Scan Files**: Click "Scan Files" to compare source and target
8. **Review Changes**: Check files, view diffs, see import replacements
9. **Deploy**: Select files and click "Deploy Selected"

After deploying, switch to **Tab 2 (Reports & Changelog)** to review the history or **Tab 3 (Release Notes)** to generate release documentation.

## 📋 Features

### Multi-Source Support
- **BASELINE**: Base implementation for all products
- **BASELINE_DMR**: DMR-specific implementation
- **PPV**: Product Performance Validation tools

### Product Selection (New!)
- **GNR, CWF, DMR**: Select your target product
- **Auto-filtering**: Only shows files relevant to selected product
- **Configuration persistence**: Saves settings per product

### Selective Deployment
- Deploy **DebugFramework** or **S2T** independently
- Visual checkbox selection (☐/☑)
- Space bar to toggle selection
- Column header to toggle all visible

### Smart Filtering
- **Text filter**: Search by filename
- **Show only changes**: Hide identical files
- **Show only selected**: Show only checked files
- **Show files with replacements**: Filter files that have import rules

### CSV Generation
- **Generate from UI**: Click "Generate..." in the Import Replacement or File Rename CSV row
- **Product-aware templates**: Automatically matches selected product
- **Auto-load**: Generated CSVs are loaded immediately
- **Customizable**: Change prefix, filename, and location

### Import Replacement
- Load CSV files with import replacement rules, or generate them directly from the UI
- Automatically applies during deployment
- See which files will be modified
- Preview replacements before deploying

### Deployment History & Changelog
- Every deployment appends an entry to `deployment_changelog.json` and `CHANGELOG.md`
- Tab 2 shows a scrollable history; click any entry to open its CSV report

### Validation Agent
- Click "Validate & Review..." to run `deploy_agent.py` from within the UI
- Streams syntax validation, lint, and test results to an in-app log window
- Can create a draft PR via the `gh` CLI

### File Comparison
- MD5 hash comparison for exact matches
- Similarity scoring (0-100%)
- Color-coded status:
  - 🔵 **Blue**: New files
  - 🟠 **Orange**: Minor changes (30-90% similar)
  - 🔴 **Red**: Major changes (<30% similar)
  - ⚫ **Gray**: Identical files

### Safety Features
- Automatic backup before deployment
- Warning for major changes
- Deployment summary with statistics
- Error handling and reporting

## 🔄 Import Replacement

### Generate CSV Templates

#### From the UI (Recommended ⭐)

1. Select your product (GNR, CWF, or DMR)
2. Click the **"Generate..."** button in the Import Replacement CSV section
3. Review the dialog and customize if needed
4. Click **"Generate"**
5. CSV is created and loaded automatically!

### CSV Format

The import replacement CSV must have these columns:

| Column | Required | Description |
|--------|----------|-------------|
| `old_import` | Yes | Original import statement or path |
| `new_import` | Yes | Replacement import statement or path |
| `description` | No | Human-readable description |
| `enabled` | No | "yes" or "no" (default: "yes") |

**Example CSV:**

```csv
old_import,new_import,description,enabled
from DebugFramework.SystemDebug import,from DebugFramework.GNRSystemDebug import,Product-specific SystemDebug,yes
import DebugFramework.SystemDebug,import DebugFramework.GNRSystemDebug as SystemDebug,GNR variant import,yes
users.gaespino.dev.DebugFramework.SystemDebug,users.gaespino.DebugFramework.GNRSystemDebug,Path replacement,yes
from S2T.dpmChecks import,from S2T.GNRdpmChecks import,Product-specific dpmChecks,yes
```

### Common Replacement Patterns

#### Module Name Changes
```csv
old_import,new_import,description
from S2T.dpmChecks import,from S2T.GNRdpmChecks import,GNR-specific dpmChecks
```

#### Path Replacements
```csv
old_import,new_import,description
users.gaespino.dev.DebugFramework,users.gaespino.DebugFramework.GNR,Path update
```

#### Import with Alias
```csv
old_import,new_import,description
import DebugFramework.SystemDebug,import DebugFramework.GNRSystemDebug as SystemDebug,Alias import
```

## 📝 File Renaming

### Generate File Rename CSV

#### From the UI (Recommended ⭐)

1. Select your product (GNR, CWF, or DMR)
2. Click the **"Generate..."** button in the File Rename CSV section
3. Review the dialog and customize if needed
4. Click **"Generate"**
5. CSV is created, loaded, and files are rescanned automatically!

### CSV Format

```csv
old_file,new_file,old_name,new_name,description,update_imports,enabled
DebugFramework/SystemDebug.py,DebugFramework/GNRSystemDebug.py,SystemDebug.py,GNRSystemDebug.py,Rename to GNR variant,yes,yes
```

### What Happens During Deployment

When file rename CSV is loaded:

1. **Files are renamed** according to CSV rules
2. **Imports are updated** in ALL deployed files (if `update_imports=yes`)
3. **Tree view shows ✓** for files that will be renamed
4. **Report includes** all rename changes with line numbers

## 🎯 Use Cases

### Deploy BASELINE to GNR

1. **Source**: BASELINE
2. **Deploy**: DebugFramework
3. **Target**: `S2T/BASELINE_GNR/DebugFramework`
4. **CSV**: Load `import_replacement_gnr.csv`
5. Scan and deploy

### Deploy S2T Only

1. **Source**: BASELINE
2. **Deploy**: S2T
3. **Target**: Product-specific S2T directory
4. **CSV**: Load product-specific CSV
5. Scan and deploy

### Deploy DMR Variant

1. **Source**: BASELINE_DMR
2. **Deploy**: DebugFramework or S2T
3. **Target**: DMR-specific directory
4. **CSV**: Load `import_replacement_dmr.csv`
5. Scan and deploy

### Deploy PPV Tools

1. **Source**: PPV
2. **Deploy**: PPV (automatically selected)
3. **Target**: Product-specific PPV location
4. **CSV**: Optional
5. Scan and deploy

## 🎨 GUI Components

The tool uses a 3-tab `ttk.Notebook` layout (minimum 1100×700, fully resizable).

### Tab 1 — Deploy

**Source Configuration panel** (top):
- Source radio buttons: BASELINE / BASELINE_DMR / PPV
- Deployment type: DebugFramework / S2T / PPV
- Product: GNR / CWF / DMR
- Target directory picker
- Import replacement CSV picker + Generate button
- File rename CSV picker + Generate button
- Manifest JSON picker

**File list panel** (left):
- Checkboxes, status, similarity %, replacement count
- Text filter, Show only changes, Show only selected

**Details panel** (right):
- File path, status, similarity score
- Import replacements that will be applied
- Color-coded unified diff preview

**Bottom bar**:
- Status / file counts
- Export Selection, Scan Files, Validate & Review…, Deploy Selected

### Tab 2 — Reports & Changelog
- Scrollable deployment history list
- Click any entry → opens its CSV report in the default application
- "View Changelog" button → opens `CHANGELOG.md`

### Tab 3 — Release Notes
- Generate and edit release notes from deployment history
- Save draft, export to HTML
- Create draft PR via `gh` CLI

## 🔧 Configuration

### Config File: `deploy_config.json`

```json
{
  "paths": {
    "baseline": "C:\\Git\\Automation\\Automation\\S2T\\BASELINE",
    "baseline_dmr": "C:\\Git\\Automation\\Automation\\S2T\\BASELINE_DMR",
    "ppv": "C:\\Git\\Automation\\Automation\\PPV",
    "backup_base": "C:\\Git\\Automation\\Automation\\DEVTOOLS\\backups"
  },
  "settings": {
    "similarity_threshold": 0.3
  }
}
```

### Similarity Threshold

Files with similarity below this threshold are flagged as "major changes":
- **0.3 (30%)**: Default - conservative
- **0.5 (50%)**: More permissive
- **0.1 (10%)**: Very conservative

## 📦 Backup System

Backups are automatically created before deployment:

```
DEVTOOLS/backups/
  ├── 20251209_143022/    # Timestamp folder
  │   ├── S2T/
  │   │   └── dpmChecks.py
  │   └── DebugFramework/
  │       └── SystemDebug.py
  └── 20251209_151533/
      └── ...
```

## ⚠️ Important Notes

### Major Changes Warning
Files with < 30% similarity trigger a warning:
- ⚠️ Review carefully before deploying
- Check diff preview
- Verify import replacements are correct

### Import Replacement Caveats
- Only applies to `.py` files
- Uses simple string replacement (not AST parsing)
- Test replacements on a few files first
- Keep CSV rules specific to avoid unintended matches

### Source Directory Structure
The tool expects this structure:

```
BASELINE/
  ├── DebugFramework/
  │   ├── SystemDebug.py
  │   └── ...
  └── S2T/
      ├── dpmChecks.py
      └── ...

BASELINE_DMR/
  ├── DebugFramework/
  └── S2T/

PPV/
  ├── gui/
  ├── parsers/
  └── ...
```

## 🐛 Troubleshooting

### "Source path does not exist"
- Check source selection matches your workspace structure
- Verify deployment type (DebugFramework/S2T) exists in source

### Import replacements not applied
- Verify CSV format (see CSV Format section)
- Check `enabled` column is "yes"
- Ensure Python files (`.py`) are being deployed
- Use validate mode to check CSV

### Files showing as "major changes" incorrectly
- Check if import replacements affect similarity
- Review diff preview for actual differences
- Adjust similarity threshold in config

### Deployment fails
- Check write permissions on target directory
- Verify disk space for backups
- Review error messages in dialog

## 📚 Advanced Usage

### Export Selection List
1. Select files to deploy
2. Click "Export Selection"
3. Save as CSV or TXT
4. Use for documentation or review

### Batch Deployment Script
For automated deployments:

```python
from deploy_universal import FileComparer, ImportReplacer

replacer = ImportReplacer()
replacer.load_from_csv("import_replacement_gnr.csv")

# Compare and deploy
# (See deploy_universal.py source for API)
```

### Custom Filters
Combine multiple filters:
- Text filter: "dpm"
- Show only changes: ON
- Show files with replacements: ON

This shows only changed files named "dpm*" that have import replacements.

## 🔗 Related Tools

- **deploy_agent.py**: CLI validation agent — syntax, lint, tests, draft PR
- **analyze_imports.py**: Import analysis for creating CSV templates
- **generate_release_notes.py**: Release notes automation engine

## 📝 Version History

### v3.0.0 (February 23, 2026)
- 3-tab notebook UI: Deploy / Reports & Changelog / Release Notes
- Deployment changelog (JSON + Markdown auto-append on every deploy)
- Validation agent UI (`ValidationAgentDialog`)
- Draft PR creation via `gh` CLI
- Quick test mode (pytest -x -q)
- Fully resizable window (min 1100x700)

### v2.0.0 (December 9, 2025)
- Universal deployment for BASELINE/BASELINE_DMR/PPV
- Import replacement from CSV
- Selective S2T/DebugFramework deployment
- CSV generation from UI
- Enhanced filtering and selection
- Deployment manifests for test/dev file filtering

## 🆘 Support

For issues or questions:
1. Check troubleshooting section
2. Review CSV format and validation
3. Test with small file subset first
4. Check backups if deployment goes wrong

## 📄 License

Internal Intel tool - for authorized use only.
