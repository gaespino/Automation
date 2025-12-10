# Universal Deployment Tool - Update Notes

## 🆕 New Features (v2.1.0)

### 1. Product Selection
Select your target product (GNR, CWF, DMR) to automatically filter product-specific files.

```
┌─────────────────────────────────────────────┐
│ Product: ● GNR  ○ CWF  ○ DMR                │
└─────────────────────────────────────────────┘
```

**Benefits:**
- Only deploys files relevant to selected product
- Automatically filters product-specific folders
- Prevents deploying wrong product variants

### 2. Product-Specific Folder Filtering

The tool now intelligently filters files based on product selection:

**Filtered Folders:**
- `product_specific/GNR/` → Only included for GNR
- `product_specific/CWF/` → Only included for CWF
- `product_specific/DMR/` → Only included for DMR
- Any folder named `GNR`, `CWF`, or `DMR`

**Example:**
```
Source Structure:
S2T/
  ├── product_specific/
  │   ├── GNR/
  │   │   └── gnr_utils.py      ← Only for GNR
  │   ├── CWF/
  │   │   └── cwf_utils.py      ← Only for CWF
  │   └── DMR/
  │       └── dmr_utils.py      ← Only for DMR
  └── CoreManipulation.py       ← Included for all

When GNR is selected:
✅ CoreManipulation.py (included)
✅ product_specific/GNR/gnr_utils.py (included)
❌ product_specific/CWF/cwf_utils.py (skipped)
❌ product_specific/DMR/dmr_utils.py (skipped)
```

### 3. Configuration Management

**Auto-Save:**
- Checkbox to enable/disable automatic config saving
- Saves configuration whenever you change settings
- Each product has its own saved configuration

**Manual Save:**
- "Save Config" button to save current state
- Saves for the currently selected product

**Persistent Settings per Product:**
Each product (GNR/CWF/DMR) remembers:
- ✅ Source type (BASELINE/BASELINE_DMR/PPV)
- ✅ Deployment type (DebugFramework/S2T)
- ✅ Target directory
- ✅ Import replacement CSV
- ✅ Selected files list

### 4. Configuration File Structure

The tool now saves to `deploy_config.json`:

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
  },
  "product_configs": {
    "GNR": {
      "source_type": "BASELINE",
      "deployment_type": "DebugFramework",
      "target_base": "C:\\Git\\Automation\\Automation\\S2T\\BASELINE_GNR\\DebugFramework",
      "replacement_csv": "C:\\Git\\Automation\\Automation\\DEVTOOLS\\import_replacement_gnr.csv",
      "selected_files": ["SystemDebug.py", "FileHandler.py"]
    },
    "CWF": {
      "source_type": "BASELINE",
      "deployment_type": "S2T",
      "target_base": "C:\\Git\\Automation\\Automation\\S2T\\BASELINE_CWF\\S2T",
      "replacement_csv": "C:\\Git\\Automation\\Automation\\DEVTOOLS\\import_replacement_cwf.csv",
      "selected_files": []
    },
    "DMR": {
      "source_type": "BASELINE_DMR",
      "deployment_type": "DebugFramework",
      "target_base": "C:\\Git\\Automation\\Automation\\S2T\\BASELINE_DMR_TARGET\\DebugFramework",
      "replacement_csv": "C:\\Git\\Automation\\Automation\\DEVTOOLS\\import_replacement_dmr.csv",
      "selected_files": []
    }
  }
}
```

## 🎯 Updated Workflow

### First Time Setup (Per Product)

1. **Select Product**: Click GNR/CWF/DMR radio button
2. **Configure Source**: Choose BASELINE/BASELINE_DMR/PPV
3. **Configure Deployment**: Choose DebugFramework/S2T
4. **Select Target**: Browse to product directory
5. **Load CSV**: Select product-specific CSV
6. **Enable Auto-Save**: Check "Auto-save configuration"
7. **Scan Files**: Click "Scan Files"
8. **Deploy**: Select and deploy files

### Subsequent Use

1. **Select Product**: Click GNR/CWF/DMR
2. **Auto-Loaded**: All settings restored automatically
3. **Scan Files**: Click "Scan Files"
4. **Deploy**: Previous selections remembered

## 🔄 Switching Between Products

```
Working on GNR → Select files → Switch to CWF
                                    ↓
                            CWF config auto-loads
                                    ↓
                            Different target directory
                            Different CSV
                            Different selections
                                    ↓
                            Switch back to GNR
                                    ↓
                            GNR config restored
```

## 📊 Status Bar Updates

The status bar now shows:
```
Found 45 files for GNR (skipped 23 other product files)
```

This helps you see:
- How many files match your product selection
- How many files were filtered out

## 🎨 Updated GUI

```
┌────────────────────────────────────────────────────────────┐
│ Product: ● GNR  ○ CWF  ○ DMR  ☑ Auto-save  [Save Config]  │
├────────────────────────────────────────────────────────────┤
│ Source:  ● BASELINE  ○ BASELINE_DMR  ○ PPV                 │
│ Deploy:  ● DebugFramework  ○ S2T  ○ PPV                    │
│ Target:  C:\...\BASELINE_GNR\DebugFramework [Select...]    │
│ CSV:     import_replacement_gnr.csv [Load...] [Clear]      │
└────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration Tips

### Auto-Save Enabled
- Changes saved immediately when you modify settings
- Switch products without losing work
- Previous selections restored when switching back

### Auto-Save Disabled
- Make temporary changes without affecting saved config
- Click "Save Config" when ready to persist changes
- Useful for testing different configurations

### Manual Configuration Edit
You can manually edit `deploy_config.json` to:
- Set default paths
- Pre-configure all products
- Share configurations with team

## 📋 Use Case Examples

### Example 1: Deploy BASELINE to Multiple Products

```
1. Select GNR
   - Target: .../BASELINE_GNR/DebugFramework
   - CSV: import_replacement_gnr.csv
   - Scan → Select → Deploy

2. Select CWF
   - Target: .../BASELINE_CWF/DebugFramework
   - CSV: import_replacement_cwf.csv
   - Scan → Select → Deploy

3. Select DMR
   - Target: .../BASELINE_DMR_TARGET/DebugFramework
   - CSV: import_replacement_dmr.csv
   - Scan → Select → Deploy
```

Each product configuration is remembered!

### Example 2: Product-Specific Development

```
Working on GNR-specific feature:
  Product: GNR
  Source: BASELINE
  Deploy: DebugFramework
  Files: Only GNR-specific files shown
  Deploy: Only GNR files deployed

Testing on CWF:
  Switch to: CWF
  Auto-loads: CWF configuration
  Files: Only CWF-specific files shown
  Deploy: Only CWF files deployed
```

## 🛡️ Safety Features

### Product Filtering Prevents Errors
- Can't accidentally deploy GNR files to CWF target
- Product-specific folders automatically filtered
- Status bar shows skipped files count

### Configuration Isolation
- Each product has separate saved state
- Switching products doesn't lose selections
- Can work on multiple products in same session

### Backup System Still Active
- All deployments create backups
- Backups include product name in status
- Easy rollback if needed

## 📝 Migration from v2.0.0

If you were using v2.0.0:

1. **First Launch**: Tool creates default product configs
2. **Set Up Products**: Configure each product once
3. **Enable Auto-Save**: Check the auto-save checkbox
4. **Continue Working**: All settings now persist

Your old `deploy_config.json` will be automatically upgraded with product configs.

## 🎓 Best Practices

### 1. One-Time Setup
Configure each product thoroughly once:
- Set correct target directories
- Load appropriate CSV files
- Test with a few files first

### 2. Use Auto-Save
Enable auto-save to avoid losing configuration:
- Settings persist across restarts
- Switch between products freely
- Previous selections restored

### 3. Product-Specific CSVs
Use the correct CSV for each product:
- GNR → `import_replacement_gnr.csv`
- CWF → `import_replacement_cwf.csv`
- DMR → `import_replacement_dmr.csv`

### 4. Verify Filtering
Check status bar for skipped files:
- Confirms product filtering is working
- Shows how many files were filtered
- Prevents accidental deployments

## 🔄 Version Comparison

| Feature | v2.0.0 | v2.1.0 |
|---------|---------|---------|
| Multi-source | ✅ | ✅ |
| Import replacement | ✅ | ✅ |
| Target selection | ✅ | ✅ |
| Product selection | ❌ | ✅ New! |
| Product filtering | ❌ | ✅ New! |
| Config per product | ❌ | ✅ New! |
| Auto-save | ❌ | ✅ New! |
| Selection memory | ❌ | ✅ New! |

## 🚀 Quick Start with New Features

### First Time
```bash
1. Launch: launch_deploy_universal.bat
2. Select: GNR
3. Configure: Source, Deployment, Target, CSV
4. Enable: ☑ Auto-save configuration
5. Scan: Click "Scan Files"
6. Notice: Status shows "Found X files for GNR (skipped Y)"
7. Deploy: Select and deploy files
```

### Next Time
```bash
1. Launch: launch_deploy_universal.bat
2. Select: GNR (config auto-loads!)
3. Scan: Click "Scan Files"
4. Deploy: Previous selections remembered
```

## 📞 Support

For questions about new features:
- Check the updated `UNIVERSAL_DEPLOY_GUIDE.md`
- Review `UNIVERSAL_DEPLOY_QUICKREF.md`
- Examine `deploy_config.json` structure

---

**Version**: 2.1.0  
**Date**: December 9, 2025  
**New Features**: Product selection, Product filtering, Configuration management
