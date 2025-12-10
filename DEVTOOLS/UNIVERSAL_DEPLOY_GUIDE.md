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

### Basic Workflow

1. **Select Source**: Choose BASELINE, BASELINE_DMR, or PPV
2. **Select Deployment Type**: Choose S2T or DebugFramework (or PPV for PPV source)
3. **Select Target**: Click "Select Target..." and choose destination directory
4. **Load Import Replacements** (Optional): Load CSV with replacement rules
5. **Scan Files**: Click "Scan Files" to compare source and target
6. **Review Changes**: Check files, view diffs, see import replacements
7. **Deploy**: Select files and click "Deploy Selected"

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

### CSV Generation (New! ⭐)
- **Generate from UI**: Create import and rename CSVs without command line
- **Product-aware templates**: Automatically matches selected product
- **Auto-load**: Generated CSVs are loaded immediately
- **Customizable**: Change prefix, filename, and location
- See [CSV_GENERATION_GUIDE.md](CSV_GENERATION_GUIDE.md) for details

### Import Replacement
- Load CSV files with import replacement rules
- **Or generate them** directly from the UI (New!)
- Automatically applies during deployment
- See which files will be modified
- Preview replacements before deploying

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

See [CSV_GENERATION_GUIDE.md](CSV_GENERATION_GUIDE.md) for detailed instructions.

#### From Command Line (Alternative)

```bash
# Generate GNR-specific replacements
python generate_import_replacement_csv.py --mode product --product GNR

# Generate CWF-specific replacements
python generate_import_replacement_csv.py --mode product --product CWF

# Generate DMR-specific replacements
python generate_import_replacement_csv.py --mode product --product DMR
```

#### Generate Custom Template

```bash
python generate_import_replacement_csv.py --mode template --target-prefix GNR
```

#### Generate from Import Analysis

```bash
python generate_import_replacement_csv.py \
    --mode analysis \
    --analysis BASELINE_IMPORTS_DETAILED.md \
    --source-prefix "DebugFramework" \
    --target-prefix "GNR"
```

#### Validate Existing CSV

```bash
python generate_import_replacement_csv.py \
    --mode validate \
    --validate import_replacement_gnr.csv
```

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

See [FILE_RENAME_GUIDE.md](FILE_RENAME_GUIDE.md) for detailed instructions.

#### From Command Line (Alternative)

```bash
# Generate GNR-specific renames
python generate_file_rename_csv.py --mode product --product GNR

# Generate CWF-specific renames
python generate_file_rename_csv.py --mode product --product CWF

# Generate DMR-specific renames
python generate_file_rename_csv.py --mode product --product DMR
```

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

### Header
- **Source Selection**: Radio buttons for BASELINE/BASELINE_DMR/PPV
- **Deployment Type**: Radio buttons for DebugFramework/S2T/PPV
- **Target Directory**: Selection and display
- **Import CSV**: Load and manage replacement rules

### File List (Left Panel)
- **Checkboxes**: Visual selection indicators
- **Status Column**: File comparison status
- **Similarity**: Percentage match
- **Replacements**: Number of import rules that apply
- **Filters**: Text search and smart filters

### Details Panel (Right)
- **File Information**: Path, status, similarity
- **Import Replacements**: List of rules that will apply
- **Diff Preview**: Side-by-side comparison with color coding

### Bottom Bar
- **Status Display**: Current operation and selection count
- **Export Selection**: Save selected files to CSV
- **Deploy Selected**: Execute deployment

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

- **deploy_ppv.py**: Original PPV-specific deployment tool
- **analyze_imports.py**: Import analysis for creating CSV templates
- **generate_import_replacement_csv.py**: CSV template generator

## 📝 Version History

### v2.0.0 (December 9, 2025)
- Universal deployment for BASELINE/BASELINE_DMR/PPV
- Import replacement from CSV
- Selective S2T/DebugFramework deployment
- CSV template generator
- Enhanced filtering and selection

## 🆘 Support

For issues or questions:
1. Check troubleshooting section
2. Review CSV format and validation
3. Test with small file subset first
4. Check backups if deployment goes wrong

## 📄 License

Internal Intel tool - for authorized use only.
