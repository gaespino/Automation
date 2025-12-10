# File Renaming and Deployment Reporting - Update v2.2.0

## 🆕 New Features

### 1. File Renaming System
Automatically rename files during deployment (e.g., `SystemDebug.py` → `GNRSystemDebug.py`)

### 2. Import Update for Renamed Files
When files are renamed, automatically update imports in other files to reference the new names

### 3. Comprehensive Deployment Reports
Generate detailed CSV reports with:
- All deployed files with line-by-line changes
- Import replacements applied
- File rename changes
- Product-filtered files
- Error tracking

## 📋 File Rename CSV Format

### Structure
```csv
old_file,new_file,old_name,new_name,description,update_imports,enabled
DebugFramework/SystemDebug.py,DebugFramework/GNRSystemDebug.py,SystemDebug.py,GNRSystemDebug.py,Rename to GNR variant,yes,yes
```

### Columns

| Column | Required | Description |
|--------|----------|-------------|
| `old_file` | Yes | Original relative file path |
| `new_file` | Yes | New relative file path |
| `old_name` | Yes | Original filename |
| `new_name` | Yes | New filename |
| `description` | No | Human-readable description |
| `update_imports` | No | "yes" to update imports (default: "no") |
| `enabled` | No | "yes" or "no" (default: "yes") |

### Example: SystemDebug Rename

**File Rename CSV:**
```csv
old_file,new_file,old_name,new_name,description,update_imports,enabled
DebugFramework/SystemDebug.py,DebugFramework/GNRSystemDebug.py,SystemDebug.py,GNRSystemDebug.py,GNR variant,yes,yes
```

**What Happens:**

1. **File is Renamed:**
   - Source: `BASELINE/DebugFramework/SystemDebug.py`
   - Deployed as: `TARGET/DebugFramework/GNRSystemDebug.py`

2. **Imports are Updated** (because `update_imports=yes`):
   
   **In other files:**
   ```python
   # Before
   from DebugFramework.SystemDebug import Config
   import DebugFramework.SystemDebug
   
   # After deployment
   from DebugFramework.GNRSystemDebug import Config
   import DebugFramework.GNRSystemDebug
   ```

## 🛠️ Generate File Rename CSVs

### Generate Product-Specific Templates

```bash
# GNR
python generate_file_rename_csv.py --mode product --product GNR

# CWF
python generate_file_rename_csv.py --mode product --product CWF

# DMR
python generate_file_rename_csv.py --mode product --product DMR
```

**Output:**
- `file_rename_gnr.csv`
- `file_rename_cwf.csv`
- `file_rename_dmr.csv`

### Analyze Directory for Rename Suggestions

```bash
python generate_file_rename_csv.py \
    --mode analysis \
    --directory C:\Git\Automation\Automation\S2T\BASELINE \
    --product GNR
```

**Output:** Analyzes all Python files and suggests renames based on common patterns

### Validate File Rename CSV

```bash
python generate_file_rename_csv.py \
    --mode validate \
    --validate file_rename_gnr.csv
```

**Output:**
```
✅ CSV validation passed: file_rename_gnr.csv
   Total rules: 4
   Enabled: 4
   Disabled: 0

📋 Sample renames:
   1. SystemDebug.py → GNRSystemDebug.py
      (will update imports)
   2. dpmChecks.py → GNRdpmChecks.py
      (will update imports)
```

## 🎯 Using File Rename in Deployment Tool

### GUI Workflow

1. **Load File Rename CSV**
   ```
   File Rename CSV: None [Load CSV...] [Clear]
                           ↓ Click
                   Select file_rename_gnr.csv
   ```

2. **Scan Files**
   - Files that will be renamed show ✓ in "Rename" column
   - Display name shows new filename (italicized)

3. **Review Changes**
   - Click file to see rename details
   - Shows: Old name → New name
   - Shows: "Will update imports in this file"

4. **Deploy**
   - Files are deployed with new names
   - Imports are automatically updated

### Tree View Display

```
☑  File                        Status  Similar  Replace  Rename
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
▼  DebugFramework/
   ☑  GNRSystemDebug.py        Minor   85%      2 rules  ✓
      (shown in italics = renamed)
   ☑  GNRTestFramework.py      New     -        -        ✓
   ☐  FileHandler.py           Minimal 95%      1 rule   -
```

## 📊 Deployment Report

### Report Generation

After each deployment, a comprehensive CSV report is automatically generated:

**Filename:** `deployment_report_YYYYMMDD_HHMMSS.csv`

### Report Structure

#### 1. Header Section
```csv
Deployment Report
Timestamp,20251209_143022
Product,GNR
Source Type,BASELINE
Deployment Type,DebugFramework
Target,C:\...\BASELINE_GNR\DebugFramework
Total Files Scanned,145
Product Filtered,23
Deployed Successfully,45
Errors,0
```

#### 2. Deployed Files Section
```csv
DEPLOYED FILES
Source File,Target File,Renamed,Old Name,New Name,Status,Similarity,Import Replacements,Filename Import Updates,Import Change Lines,Rename Change Lines
DebugFramework/SystemDebug.py,DebugFramework/GNRSystemDebug.py,Yes,SystemDebug.py,GNRSystemDebug.py,Minor,85%,"from DebugFramework.SystemDebug → from DebugFramework.GNRSystemDebug","SystemDebug → GNRSystemDebug","4, 15, 27","8, 42"
```

#### 3. Detailed Line Changes Section
```csv
DETAILED LINE CHANGES
File,Line,Change Type,Old Content,New Content
DebugFramework/SystemDebug.py,4,Import Replacement,"from DebugFramework.SystemDebug import Config","from DebugFramework.GNRSystemDebug import Config"
DebugFramework/FileHandler.py,8,Filename Import Update,"import SystemDebug","import GNRSystemDebug"
```

#### 4. Skipped Files Section
```csv
SKIPPED FILES
File,Reason,Status,Renamed,New Name
S2T/product_specific/CWF/cwf_utils.py,Product filtered,New,No,-
DebugFramework/TestMocks.py,Not selected,Identical,No,-
```

#### 5. Errors Section (if any)
```csv
ERRORS
File,Error
S2T/CoreManipulation.py,Permission denied
```

### Report Columns Explained

| Column | Description |
|--------|-------------|
| **Source File** | Original file path |
| **Target File** | Deployed file path (includes rename) |
| **Renamed** | Yes/No if file was renamed |
| **Old Name** | Original filename |
| **New Name** | New filename (if renamed) |
| **Status** | File comparison status |
| **Similarity** | How similar files are (%) |
| **Import Replacements** | Import rules applied |
| **Filename Import Updates** | Import updates due to file renames |
| **Import Change Lines** | Line numbers with import changes |
| **Rename Change Lines** | Line numbers with rename-related changes |

### View Report in GUI

After deployment:
1. **View Last Report** button is enabled
2. Click to open report viewer window
3. See summary and detailed changes
4. CSV file saved in DEVTOOLS folder

## 🎨 Complete Workflow Example

### Scenario: Deploy BASELINE to GNR with Renames

#### Step 1: Configure
```
Product: GNR
Source: BASELINE
Deploy: DebugFramework
Target: C:\...\BASELINE_GNR\DebugFramework
Import CSV: import_replacement_gnr.csv
File Rename CSV: file_rename_gnr.csv
```

#### Step 2: Scan Files
```
Found 145 files for GNR (skipped 23 other product files)

Files to rename:
  • SystemDebug.py → GNRSystemDebug.py
  • TestFramework.py → GNRTestFramework.py
  • dpmChecks.py → GNRdpmChecks.py
  • CoreManipulation.py → GNRCoreManipulation.py
```

#### Step 3: Select Files
```
☑ GNRSystemDebug.py (renamed)
  - Will apply 2 import replacements
  - Will update imports referencing this file
  
☑ FileHandler.py
  - Will update imports to use GNRSystemDebug
```

#### Step 4: Deploy
```
Deployment Summary:
  Files: 45
  Import replacements: 23 file(s)
  File renames: 4
```

#### Step 5: Review Report
**deployment_report_20251209_143022.csv** contains:

```
SystemDebug.py → GNRSystemDebug.py:
  - Import changes at lines: 4, 15, 27
  - Renamed imports in 12 other files
  
FileHandler.py:
  - Renamed import changes at lines: 8, 42
  - from SystemDebug import → from GNRSystemDebug import
```

## 🔄 Combined Operations

### File Rename + Import Replacement

When both are active, operations happen in this order:

1. **File Rename Applied**
   - `SystemDebug.py` → `GNRSystemDebug.py`

2. **Import Replacements Applied**
   - In the renamed file:
   ```python
   # Original
   from DebugFramework.SystemDebug import Config
   
   # After import replacement CSV
   from DebugFramework.GNRSystemDebug import Config
   ```

3. **Filename Import Updates Applied**
   - In other files referencing the renamed file:
   ```python
   # Original
   import SystemDebug
   
   # After filename import update
   import GNRSystemDebug
   ```

### Report Shows All Changes

```csv
File,Line,Change Type,Old,New
GNRSystemDebug.py,4,Import Replacement,"from DebugFramework.SystemDebug","from DebugFramework.GNRSystemDebug"
FileHandler.py,8,Filename Import Update,"import SystemDebug","import GNRSystemDebug"
```

## 📈 Report Statistics

### Summary Metrics in Report

- **Total Files Scanned**: All files found in source
- **Product Filtered**: Files excluded due to product selection
- **Deployed Successfully**: Files actually deployed
- **Errors**: Files that failed to deploy

### Per-File Metrics

- **Import Replacements**: Number of import rules applied
- **Filename Import Updates**: Number of imports updated due to rename
- **Import Change Lines**: Specific line numbers changed
- **Rename Change Lines**: Lines changed due to file rename

## 🛡️ Safety Features

### Comprehensive Tracking
- Every change is logged with line numbers
- Easy to trace what happened where
- Can verify all transformations

### Rollback Information
- Backup directory listed in report
- Original files preserved
- CSV report shows all changes

### Validation
- Validate CSV before using
- Preview changes before deploying
- Review report after deployment

## 💡 Best Practices

### 1. Test File Renames First
```bash
# Generate template
python generate_file_rename_csv.py --mode product --product GNR

# Edit and customize

# Validate before using
python generate_file_rename_csv.py --mode validate --validate file_rename_gnr.csv

# Test on small subset
```

### 2. Review Reports
- Always check deployment report after deployment
- Verify line changes are correct
- Look for unexpected import updates

### 3. Keep CSVs in Sync
- File rename CSV and import replacement CSV should be compatible
- If you rename SystemDebug to GNRSystemDebug:
  - File rename CSV: handles the file
  - Import replacement CSV: handles imports within the file
  - Filename import updates: handled automatically

### 4. Use Product-Specific CSVs
```
GNR: 
  - import_replacement_gnr.csv
  - file_rename_gnr.csv

CWF:
  - import_replacement_cwf.csv
  - file_rename_cwf.csv

DMR:
  - import_replacement_dmr.csv
  - file_rename_dmr.csv
```

## 🔧 Troubleshooting

### File Not Renamed
- Check CSV has `enabled=yes`
- Verify file path matches exactly
- Check rename column shows ✓ before deploying

### Imports Not Updated
- Check `update_imports=yes` in file rename CSV
- Verify import pattern matches
- Review report to see what was updated

### Report Shows Unexpected Changes
- Review both CSVs (import and file rename)
- Check line change details in report
- Verify changes are intentional

### Missing Line Numbers in Report
- Only Python files track line numbers
- Other files copied directly
- Check file extension

## 📝 CSV Examples

### Simple Rename (No Import Updates)
```csv
old_file,new_file,old_name,new_name,description,update_imports,enabled
Utils/helper.py,Utils/helper_gnr.py,helper.py,helper_gnr.py,GNR helper,no,yes
```

### Rename with Import Updates
```csv
old_file,new_file,old_name,new_name,description,update_imports,enabled
S2T/dpmChecks.py,S2T/GNRdpmChecks.py,dpmChecks.py,GNRdpmChecks.py,GNR dpmChecks,yes,yes
```

### Conditional Rename (Disabled)
```csv
old_file,new_file,old_name,new_name,description,update_imports,enabled
Config/settings.py,Config/gnr_settings.py,settings.py,gnr_settings.py,GNR settings,yes,no
```

---

**Version**: 2.2.0  
**Date**: December 9, 2025  
**New Features**: File renaming, Import updates for renames, Comprehensive deployment reports
