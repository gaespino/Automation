# Deployment Manifest Quick Start Guide

## What's New?

Your deployment tool now supports **automatic filtering of test/mock/development files** using deployment manifests! This ensures only production-ready code is deployed.

## Quick Start (3 Easy Steps)

### 1. Open Your Deployment Tool
```bash
python DEVTOOLS/deploy_universal.py
```

### 2. Configure Your Deployment
- Select **Product**: GNR, CWF, or DMR
- Select **Source**: BASELINE, BASELINE_DMR, or PPV  
- Select **Deploy**: DebugFramework, S2T, or PPV
- Click **"Select Target..."** to choose destination

### 3. Load the Manifest
Click **"Auto-Load"** button in the Deployment Manifest section.

That's it! The tool will automatically exclude:
- ❌ TestRun.py, TestMocks.py, S2TTestFramework.py
- ❌ All *Mock*.py files (HardwareMocks, S2TMocks, etc.)
- ❌ Development files (Old_code.py, notes.txt, etc.)
- ❌ Test files (test_*.py, *_test.py)
- ❌ Debug scripts and backup files

## What Each Button Does

### 🔵 **Load Manifest...** (Manual)
- Browse and select a specific manifest JSON file
- Use when you have custom manifests or need precise control

### 🔴 **Auto-Load** (Recommended)
- Automatically loads the correct manifest for your deployment type
- **DebugFramework** → `deployment_manifest_debugframework.json`
- **S2T** → `deployment_manifest_s2t.json`
- **PPV** → `deployment_manifest_ppv.json`

### ⚪ **Clear**
- Remove manifest filtering
- Shows all files (including test/mock files)
- Use when you need to see what's being filtered out

## Complete Workflow Example

### Deploying DebugFramework to GNR Production

```
1. Select Product: GNR
2. Select Source: BASELINE
3. Select Deploy: DebugFramework
4. Click "Select Target..." → Choose your production directory
5. Click "Auto-Load" in Deployment Manifest section
   ✅ Manifest loaded: debugframework
6. Click "Scan Files"
   ✅ Found 80 files for GNR (manifest excluded 15)
7. Review the file list - notice NO test/mock files!
8. Select files you want to deploy (or "Select All")
9. Click "Deploy Selected"
```

## What Gets Excluded for Each Module

### DebugFramework Exclusions
```
❌ TestRun.py
❌ TestMocks.py
❌ HardwareMocks.py
❌ S2TMocks.py
❌ S2TTestFramework.py
❌ UI/MockControlPanel.py
❌ UI/TestControlPanel.py
❌ UI/test_config.py
❌ ExecutionHandler/Old_code.py
❌ Automation_Flow/notes.txt
❌ Automation_Flow/dummy_structure.json
```

### S2T Exclusions
```
❌ All test_*.py files
❌ Non-target product folders
   (e.g., if deploying GNR, excludes CWF and DMR folders)
```

### PPV Exclusions
```
❌ MCAparser_bkup.py
❌ install_dependencies.bat/py
❌ process.ps1
❌ DebugScripts/ (entire directory)
```

## Status Bar Messages

The status bar shows what's happening:

- **"Found 80 files for GNR (manifest excluded 15)"**
  - 80 files passed all filters
  - 15 files excluded by manifest (test/mock files)
  
- **"Found 80 files for GNR (manifest excluded 15) (product filtered 5)"**
  - 80 files ready for deployment
  - 15 excluded by manifest
  - 5 excluded because they belong to other products

## Tips & Best Practices

### ✅ Always Use Auto-Load
- Click "Auto-Load" every time you change deployment type
- It ensures the correct manifest is loaded automatically

### ✅ Check the Status Message
- After scanning, verify the exclusion counts
- Example: "manifest excluded 15" is normal for DebugFramework

### ✅ Verify Before Deployment
- Scroll through the file list
- Make sure no TestRun.py or Mock files appear
- All test files should be automatically filtered

### ✅ Save Your Configuration
- Enable "Auto-save configuration" checkbox
- Your manifest selection will be remembered per product

### ❌ Don't Deploy Without Manifest
- Without a manifest, ALL files are included (including tests!)
- Always click "Auto-Load" or manually load a manifest

## Troubleshooting

### "No Manifest" Warning
**Problem**: Clicked Auto-Load but manifest file doesn't exist

**Solution**: The manifest files should be in DEVTOOLS folder:
- `deployment_manifest_debugframework.json`
- `deployment_manifest_s2t.json`
- `deployment_manifest_ppv.json`

Check that these files exist in your DEVTOOLS directory.

### "Found 0 files"
**Problem**: After loading manifest, scan shows no files

**Solution**: The manifest might be too restrictive
1. Click "Clear" to remove manifest
2. Click "Scan Files" to see all files
3. Verify source path is correct

### Test Files Still Appearing
**Problem**: Seeing TestRun.py or Mock files after loading manifest

**Solution**:
1. Click "Clear" then "Auto-Load" again
2. Click "Scan Files" to refresh
3. Verify correct manifest loaded (check manifest label)

## Understanding the Manifest Label

The label shows what's loaded:

- **"None (all files included)"** - No filtering active ⚠️
- **"debugframework"** - DebugFramework manifest active ✅
- **"s2t"** - S2T manifest active ✅
- **"ppv"** - PPV manifest active ✅

## Advanced: Custom Manifests

If you need custom filtering rules:

1. Copy an existing manifest JSON file
2. Edit the exclusion rules
3. Use "Load Manifest..." to load your custom file

See `DEPLOYMENT_MANIFEST_GUIDE.md` for manifest file format details.

## Configuration Persistence

Your manifest selection is saved when:
- "Auto-save configuration" is checked (enabled by default)
- You change products/deployment types
- You manually click "Save Config"

Next time you open the tool and select the same product, your manifest will be automatically loaded!

## Summary Checklist

Before deploying to production, verify:

- [ ] Correct product selected (GNR/CWF/DMR)
- [ ] Correct source selected (BASELINE/BASELINE_DMR/PPV)
- [ ] Correct deployment type (DebugFramework/S2T/PPV)
- [ ] Target directory selected
- [ ] **Manifest loaded** (label shows module name, not "None")
- [ ] Files scanned
- [ ] Status shows "manifest excluded X" files
- [ ] No test/mock files visible in the list
- [ ] Files selected for deployment
- [ ] Ready to click "Deploy Selected"

---

## Need Help?

- See `DEPLOYMENT_MANIFEST_GUIDE.md` for detailed documentation
- See `DEPLOYMENT_FILE_LISTS.md` for complete file lists
- Check the manifest JSON files for exclusion rules
