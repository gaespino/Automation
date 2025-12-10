# CSV Generation Guide

## Overview

The Universal Deployment Tool now includes integrated CSV generation functionality. You can create and customize import replacement and file rename CSVs directly from the deployment interface without needing to use separate command-line tools.

## Features

### 1. Import Replacement CSV Generation

Generate CSV templates for import replacement rules that map base imports to product-specific variants.

**Location in UI:** Import Replacement CSV section → "Generate..." button

**What it creates:**
- Product-specific import replacement rules
- Common patterns for SystemDebug, TestFramework, dpmChecks, CoreManipulation
- Enabled by default for immediate use

**Template includes:**
```csv
old_import,new_import,description,enabled
from DebugFramework.SystemDebug import,from DebugFramework.GNRSystemDebug import,Product-specific SystemDebug,yes
from DebugFramework import SystemDebug,from DebugFramework import GNRSystemDebug as SystemDebug,Product-specific SystemDebug alias,yes
...
```

### 2. File Rename CSV Generation

Generate CSV templates for file renaming rules that automatically rename files during deployment and update imports throughout the codebase.

**Location in UI:** File Rename CSV section → "Generate..." button

**What it creates:**
- Product-specific file rename rules
- Common patterns for core framework files
- Automatic import update enabled
- Enabled by default for immediate use

**Template includes:**
```csv
old_file,new_file,old_name,new_name,description,update_imports,enabled
DebugFramework/SystemDebug.py,DebugFramework/GNRSystemDebug.py,SystemDebug.py,GNRSystemDebug.py,Rename SystemDebug to GNRSystemDebug,yes,yes
...
```

## How to Use

### Generate Import Replacement CSV

1. **Select Product** in the main UI (GNR, CWF, or DMR)
2. Click **"Generate..."** button in the Import Replacement CSV section
3. **Review the dialog:**
   - Product Prefix: Pre-filled with selected product (e.g., "GNR")
   - Output File: Auto-named (e.g., `import_replacement_gnr.csv`)
   - Output Directory: Defaults to DEVTOOLS folder
   - Preview of template contents
4. **Customize if needed:**
   - Change product prefix for different naming conventions
   - Modify output filename
   - Select different output directory
5. Click **"Generate"**
6. **CSV is automatically:**
   - Created in the specified location
   - Loaded into the deployment tool
   - Saved in your product configuration

### Generate File Rename CSV

1. **Select Product** in the main UI (GNR, CWF, or DMR)
2. Click **"Generate..."** button in the File Rename CSV section
3. **Review the dialog:**
   - Product Prefix: Pre-filled with selected product
   - Output File: Auto-named (e.g., `file_rename_gnr.csv`)
   - Output Directory: Defaults to DEVTOOLS folder
   - Preview of template contents
4. **Customize if needed:**
   - Change product prefix
   - Modify output filename
   - Select different output directory
5. Click **"Generate"**
6. **CSV is automatically:**
   - Created in the specified location
   - Loaded into the deployment tool
   - Files are rescanned to detect renames
   - Saved in your product configuration

## Dialog Options

### Product Prefix
- **Default:** Current selected product (GNR, CWF, DMR)
- **Customizable:** You can change this to any prefix
- **Purpose:** Used to generate product-specific rules
- **Example:** "GNR" → generates GNRSystemDebug, GNRTestFramework, etc.

### Output File
- **Default:** Follows naming convention
  - Import: `import_replacement_{product}.csv`
  - Rename: `file_rename_{product}.csv`
- **Customizable:** You can specify any filename
- **Recommendation:** Keep the naming convention for organization

### Output Directory
- **Default:** DEVTOOLS folder (same location as deployment tool)
- **Customizable:** Click "Browse..." to select any directory
- **Recommendation:** Keep CSVs in DEVTOOLS for easy access

## Template Contents

### Import Replacement Template (9 rules)

The generated template includes common import patterns:

1. **SystemDebug imports** (3 variants)
   - `from DebugFramework.SystemDebug import`
   - `from DebugFramework import SystemDebug`
   - `import DebugFramework.SystemDebug`

2. **TestFramework imports** (2 variants)
   - `from DebugFramework.TestFramework import`
   - `from DebugFramework import TestFramework`

3. **S2T module imports** (3 variants)
   - `from S2T.dpmChecks import`
   - `from S2T import CoreManipulation`
   - `from S2T.CoreManipulation import`

4. **Path replacements** (1 variant)
   - `users.gaespino.dev.DebugFramework.SystemDebug`

### File Rename Template (4 rules)

The generated template includes common file renames:

1. **DebugFramework/SystemDebug.py** → `{Product}SystemDebug.py`
2. **DebugFramework/TestFramework.py** → `{Product}TestFramework.py`
3. **S2T/dpmChecks.py** → `{Product}dpmChecks.py`
4. **S2T/CoreManipulation.py** → `{Product}CoreManipulation.py`

All rules have `update_imports=yes` to automatically update references.

## Customizing Generated CSVs

After generation, you can edit the CSV files to:

### Add More Rules
```csv
old_import,new_import,description,enabled
from MyModule import MyClass,from GNRModule import MyClass,Custom import,yes
```

### Modify Existing Rules
- Change the product prefix in old/new imports
- Update descriptions for clarity
- Enable/disable specific rules

### Disable Rules Temporarily
```csv
old_import,new_import,description,enabled
from DebugFramework.SystemDebug import,from DebugFramework.GNRSystemDebug import,Product-specific SystemDebug,no
```

### Complex Patterns

**Path-based replacements:**
```csv
old_import,new_import,description,enabled
users.gaespino.dev,users.gaespino.prod,Change dev to prod path,yes
```

**Module aliasing:**
```csv
old_import,new_import,description,enabled
from OldModule import Class,from NewModule import Class as OldClass,Backward compatibility,yes
```

## Workflow Integration

### Typical Usage Pattern

1. **First Time Setup:**
   ```
   Select Product (e.g., GNR)
   → Generate Import CSV
   → Generate Rename CSV
   → Review and customize CSVs
   → Save configuration
   ```

2. **Regular Deployment:**
   ```
   Select Product
   → Configuration auto-loads
   → Scan Files
   → Review changes
   → Deploy
   → View comprehensive report
   ```

3. **Update CSVs:**
   ```
   Click "Generate..." again
   → Overwrites existing CSV
   → Auto-reloads in tool
   → Scan to see new changes
   ```

### Configuration Persistence

When you generate a CSV:
- ✅ CSV path is saved in product configuration
- ✅ Auto-loads next time you select that product
- ✅ Changes persist across sessions
- ✅ Each product has independent configuration

## Benefits Over Command-Line Tools

### Integrated Workflow
- No need to leave the deployment tool
- Immediate loading after generation
- Visual feedback and preview

### Automatic Configuration
- Generated CSVs are automatically loaded
- Configuration is saved for the selected product
- No manual file selection needed

### Product-Aware
- Templates are customized for selected product
- Default naming follows conventions
- Consistent with product selection

### Error Prevention
- No typos in product names
- Correct file paths automatically
- Validated before generation

## Examples

### Example 1: Generate GNR Import Replacement

```
1. Select Product: GNR
2. Click "Generate..." (Import section)
3. Dialog shows:
   - Product Prefix: GNR
   - Output File: import_replacement_gnr.csv
   - Output Directory: C:\Git\Automation\Automation\DEVTOOLS
4. Click "Generate"
5. Success! CSV created with 9 rules
6. CSV automatically loaded
7. Configuration saved
```

**Generated CSV includes:**
- `from DebugFramework.SystemDebug import` → `from DebugFramework.GNRSystemDebug import`
- `from S2T.dpmChecks import` → `from S2T.GNRdpmChecks import`
- etc.

### Example 2: Generate CWF File Rename

```
1. Select Product: CWF
2. Click "Generate..." (Rename section)
3. Dialog shows:
   - Product Prefix: CWF
   - Output File: file_rename_cwf.csv
   - Output Directory: C:\Git\Automation\Automation\DEVTOOLS
4. Click "Generate"
5. Success! CSV created with 4 rules
6. CSV automatically loaded
7. Files are rescanned
8. Tree view shows ✓ for rename-enabled files
```

**Generated CSV includes:**
- `SystemDebug.py` → `CWFSystemDebug.py` (with import updates)
- `TestFramework.py` → `CWFTestFramework.py` (with import updates)
- etc.

### Example 3: Custom Product Prefix

```
1. Select Product: GNR
2. Click "Generate..." (Import section)
3. Change Product Prefix to: "GNR_V2"
4. Output File: import_replacement_gnr_v2.csv
5. Click "Generate"
```

**Generated rules use GNR_V2:**
- `from DebugFramework.SystemDebug import` → `from DebugFramework.GNR_V2SystemDebug import`

## Troubleshooting

### CSV Not Loading

**Problem:** Generated CSV doesn't load automatically

**Solutions:**
1. Check the success message - verify file path
2. Manually click "Load CSV..." and select the file
3. Check file permissions in output directory
4. Verify CSV format is correct (open in text editor)

### Wrong Product Prefix

**Problem:** Generated CSV has wrong product prefix

**Solutions:**
1. Ensure correct product is selected before clicking "Generate..."
2. Customize product prefix in the dialog
3. Or edit the CSV file after generation
4. Reload the CSV in the tool

### Can't Find Generated CSV

**Problem:** CSV was generated but can't find it

**Solutions:**
1. Check the success message for file path
2. Look in DEVTOOLS folder by default
3. Check Output Directory field in dialog
4. Use Windows Explorer search

### Overwriting Existing CSV

**Problem:** Want to update existing CSV but preserve some rules

**Solutions:**
1. Backup existing CSV first
2. Generate new CSV with different name
3. Manually merge rules using text editor
4. Reload merged CSV

## Command-Line Alternative

If you prefer command-line generation, the standalone tools are still available:

```powershell
# Generate import CSV
python generate_import_replacement_csv.py --mode product --product GNR

# Generate rename CSV
python generate_file_rename_csv.py --mode product --product GNR
```

However, the integrated UI generator is recommended because:
- Automatically loads generated CSVs
- Saves configuration automatically
- Provides visual preview
- No typos in command-line arguments

## Best Practices

### 1. Generate Once Per Product

- Generate CSVs when first setting up a product
- Customize the CSVs for your specific needs
- Reuse the same CSVs for future deployments

### 2. Use Consistent Naming

- Keep default naming convention: `import_replacement_{product}.csv`
- Easier to find and manage
- Auto-loads correctly

### 3. Review Before Deploying

- After generating, click "Scan Files"
- Review the changes in the tree view
- Verify imports and renames are correct
- Test with a small subset first

### 4. Version Control Your CSVs

- Add generated CSVs to version control
- Track changes to replacement rules
- Share with team members
- Revert if needed

### 5. Customize Templates

- After first generation, edit CSVs to add project-specific rules
- Disable rules you don't need
- Add new patterns specific to your codebase

### 6. Keep CSVs in DEVTOOLS

- Default location is DEVTOOLS folder
- Keeps all deployment-related files together
- Easy to find and manage
- Consistent with tool location

## Summary

The integrated CSV generation feature provides:

✅ **Convenience:** Generate CSVs without leaving the tool  
✅ **Automation:** Auto-load and auto-configure  
✅ **Product-Aware:** Templates match selected product  
✅ **Customizable:** Change prefix, filename, location  
✅ **Preview:** See what will be generated  
✅ **Integration:** Works seamlessly with deployment workflow  
✅ **Configuration:** Saves settings per product  

Use this feature to quickly set up product-specific deployment configurations and streamline your workflow!
