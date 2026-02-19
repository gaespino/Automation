# DEVTOOLS - Development and Release Management Tools

This directory contains tools for managing deployments, generating release notes, and tracking changes across the Debug Framework projects.

---

## 📋 Release Notes Generator

**Quick Start for Release Notes:**
```powershell
.\launch_release_notes.ps1
```

or for AI/Copilot: See [QUICKSTART_RELEASE.md](deploys/QUICKSTART_RELEASE.md)

### Purpose
Automate the creation of Debug Framework release notes, including tracking documents, email drafts, and HTML versions.

### Key Files
- **launch_release_notes.ps1** - Interactive launcher script
- **generate_release_notes.py** - Core automation engine
- **deploys/QUICKSTART_RELEASE.md** - Complete guide for AI assistants
- **deploys/RELEASE_TEMPLATE.md** - Detailed 7-phase process guide
- **deploys/RELEASE_v1.7.1_Feb2026.md** - Example release document
- **deploys/RELEASE_EMAIL_v1.7.1_Feb2026.md** - Example release email

### Quick Usage
```powershell
# Interactive mode
.\launch_release_notes.ps1

# Direct command
python generate_release_notes.py --start-date 2026-01-22 --version 1.8.0 --html
```

**For AI:** This is a "skill" you can invoke. When asked to generate release notes, follow the process in [QUICKSTART_RELEASE.md](deploys/QUICKSTART_RELEASE.md).

---

## 🚀 PPV Deployment Tool

A sophisticated GUI tool for managing deployment of PPV files from the main development directory to the DebugFramework location.

## Features

### 🔍 Smart File Comparison
- **MD5 Hash Verification**: Quickly identifies identical files
- **Similarity Analysis**: Uses difflib to calculate change percentage
- **Intelligent Classification**:
  - **New File**: Doesn't exist in target
  - **Identical**: Files are exactly the same (skippable)
  - **Minimal Changes**: >90% similar
  - **Minor Changes**: 30-90% similar
  - **Major Changes**: <30% similar (flagged for review)

### 📊 Interactive File Browser
- **Tree View**: Organized by directory structure
- **Visual Checkboxes**: ☑ for selected, ☐ for unselected files
- **Click to Select**: Click checkbox column or press spacebar to toggle
- **Status Indicators**: Color-coded status for each file
  - 🔵 Blue: New files
  - 🟠 Orange: Minor changes
  - 🔴 Red: Major changes
  - ⚪ Gray: Identical files
- **Smart Filters**:
  - Text search across file names
  - Show only files with changes
  - Show only selected files
- **Bulk Selection**: Select all/deselect all with one click
- **Custom Target**: Change deployment destination on the fly

### 🔄 Side-by-Side Comparison
- **Unified Diff View**: See exactly what will change
- **Syntax Highlighting**:
  - Green for additions
  - Red for removals
- **File Details**: Size, similarity percentage, paths
- **Major Change Warnings**: Prominent alerts for significant differences

### 🔗 Dependency Analysis
- **Auto-Detection**: Scans Python imports to find dependencies
- **Module Tracking**: Identifies required modules (api, gui, parsers, utils, Decoder)
- **Batch Analysis**: Review dependencies for all selected files

### 💾 Safe Deployment
- **Automatic Backups**: Creates timestamped backups before deployment
- **Selective Deployment**: Deploy only the files you choose
- **Error Handling**: Detailed error reporting if issues occur
- **Confirmation Dialogs**: Multiple safeguards to prevent accidents

## Installation

No additional installation required! The script uses only Python standard library modules:
- tkinter (GUI)
- pathlib (Path handling)
- difflib (File comparison)
- hashlib (File hashing)
- shutil (File operations)

## Usage

### Quick Start

**Option 1: Run directly**
```powershell
cd c:\Git\Automation\Automation\DEVTOOLS
python deploy_ppv.py
```

**Option 2: Use the batch file**
```powershell
cd c:\Git\Automation\Automation\DEVTOOLS
.\launch_deploy.bat
```

### Step-by-Step Workflow

1. **Launch the Tool**
   - The tool will automatically scan all Python and JSON files in the PPV directory
   - Files are compared with the target location in S2T\BASELINE\DebugFramework\PPV

2. **Review Files**
   - Browse through the tree view to see all available files
   - Click on any file to see detailed comparison
   - Use the filter box to search for specific files
   - Enable "Show only files with changes" to hide identical files

3. **Select Files to Deploy**
   - Click the checkbox (☐) next to files to select them (☑)
   - Click the checkbox column header to toggle all visible files
   - Use "Select All" or "Deselect All" for bulk operations
   - Press spacebar to toggle selection of highlighted files
   - Use "Show only selected" filter to review your selection

4. **Check Dependencies** (Optional)
   - Click "View Dependencies" to see what modules your selected files depend on
   - Ensure all dependencies are included in your selection

5. **Deploy**
   - Click "Deploy Selected"
   - Review any major change warnings
   - Confirm the deployment
   - Files are backed up automatically before deployment

### Understanding Similarity Scores

- **100%**: Files are identical (green checkmark)
- **90-99%**: Minimal changes (few lines modified)
- **30-89%**: Minor changes (moderate modifications)
- **0-29%**: Major changes ⚠️ (significant differences - review carefully!)

### Backup Location

All backups are stored in:
```
c:\Git\Automation\Automation\DEVTOOLS\backups\{timestamp}\
```

Format: `YYYYMMDD_HHMMSS` (e.g., `20251209_143022`)

## Configuration

Edit these constants at the top of `deploy_ppv.py` to customize:

```python
SOURCE_BASE = Path(r"c:\Git\Automation\Automation\PPV")
TARGET_BASE = Path(r"c:\Git\Automation\Automation\S2T\BASELINE\DebugFramework\PPV")
BACKUP_BASE = Path(r"c:\Git\Automation\Automation\DEVTOOLS\backups")
SIMILARITY_THRESHOLD = 0.3  # Below 30% is "major changes"
```

## Current Deployment Status

Based on the scan, the DebugFramework PPV **does NOT include**:
- ❌ `ExperimentBuilder.py` (in main PPV only)
- ❌ `configs/` directory (configuration JSON files)
- ❌ `install_dependencies.py` / `.bat`
- ❌ `requirements.txt`
- ❌ `README.md`
- ❌ `process.ps1`
- ❌ `.vscode/` configuration

The DebugFramework PPV **includes**:
- ✅ `run.py`
- ✅ `api/` directory
- ✅ `gui/` directory (except ExperimentBuilder.py)
- ✅ `parsers/` directory
- ✅ `utils/` directory
- ✅ `Decoder/` directory
- ✅ `DebugScripts/` directory

## Tips & Best Practices

### 🎯 Selective Deployment
Don't deploy everything! The DebugFramework likely doesn't need:
- Configuration files (handled separately)
- Installation scripts
- Development tools (ExperimentBuilder)
- Documentation files

### ⚠️ Handle Major Changes Carefully
When you see "Major Changes" warnings:
1. Review the diff carefully
2. Check if the target has custom modifications
3. Consider manual merge if needed
4. Test thoroughly after deployment

### 🔄 Regular Updates
- Run the tool regularly to keep code in sync
- Review changes before deploying to understand what's new
- Keep backups for easy rollback

### 🧪 Test After Deployment
Always test the DebugFramework after deploying changes:
```powershell
cd c:\Git\Automation\Automation\S2T\BASELINE\DebugFramework\PPV
python run.py
```

## Troubleshooting

### "Source/Target directory not found"
- Verify paths in the configuration section
- Ensure both directories exist

### "Permission denied" errors
- Check file is not open in another application
- Run PowerShell as Administrator if needed

### Files not showing up
- Click "Refresh" to rescan
- Check file extensions (only .py and .json)
- Verify files exist in source directory

### Deployment failed
- Check the backup directory - your files are safe!
- Review error messages
- Manually copy problematic files if needed

## Version History

### v1.0.0 (December 9, 2025)
- Initial release
- File comparison with similarity detection
- Interactive GUI with tree view
- Dependency analysis
- Automatic backups
- Selective deployment

## Future Enhancements

Potential features for future versions:
- [ ] Configuration profiles for different targets
- [ ] Rollback functionality from backups
- [ ] Export comparison reports
- [ ] Command-line mode for automation
- [ ] Git integration for change tracking
- [ ] Schedule automated deployments

## Support

For issues or questions:
1. Check this README
2. Review the inline documentation in `deploy_ppv.py`
3. Contact the development team

---

**Author**: GitHub Copilot
**Date**: December 9, 2025
**License**: Internal Use Only
