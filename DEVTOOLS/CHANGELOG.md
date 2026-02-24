# Changelog

All notable changes to the **Universal Central Deployment Tool** are documented here.
Deployment entries are appended automatically after each deploy operation.

---

## [3.0.0] - 2026-02-23

### Added
- **Tabbed UI** (`ttk.Notebook`) with three tabs: Deploy / Reports & Changelog / Release Notes
- **Fully resizable** window with `minsize(1100, 700)` — works on 1280×720 and larger
- **Deployment Changelog** — every deploy appends to `deployment_changelog.json` (JSON) and this file (Markdown)
- **Reports & Changelog tab** — deployment history listbox + CHANGELOG.md viewer
- **Release Notes tab** — GUI front-end for `generate_release_notes.py`; includes Markdown editor, HTML export, and Draft PR creation
- **Validate & Review button** — opens `ValidationAgentDialog` which runs `deploy_agent.py` with live streaming output
- **`deploy_agent.py`** — standalone validation + PR script (syntax check, linting, quick tests, draft PR via `gh` CLI)
- **`deploy_validator.agent.md`** — GitHub Copilot agent mode definition (in `.github/agents/`)
- Horizontal scrollbar added to file tree
- `_run_agent_command()` helper for streaming subprocess output into Toplevel windows
- `open_csv_report()` button in Reports tab
- `export_release_html()` converts Markdown release docs to self-contained HTML (stdlib only)

### Changed
- Window title updated to "Universal Central Deployment Tool"
- `setup_ui()` fully restructured into `_setup_deploy_tab()`, `_setup_reports_tab()`, `_setup_release_tab()`
- Source Configuration panel converted from `pack`-stacked rows to compact `grid` layout (fits smaller screens)
- `self.report_button` stored as direct `ttk.Button` reference (replaces fragile `children[]` lookup)
- Button labels shortened in CSV row for horizontal fit

### Future Enhancements Completed
- [x] Syntax validation before deployment (`deploy_agent.py --validate`)
- [x] Export comparison reports (HTML export in Release Notes tab)
- [x] Deployment history log (`deployment_changelog.json`)
- [x] Git integration / PR creation (`deploy_agent.py --pr`)

---

## [2.0.0] - 2025-12-09

### Added
- Universal deployment tool replacing `deploy_ppv.py`
- Multi-product support (GNR, CWF, DMR)
- Multiple source types (BASELINE, BASELINE_DMR, PPV)
- Import replacement from CSV configuration
- File rename CSV support
- Deployment manifest (JSON) filtering
- CSV template generator dialog
- Per-product config persistence (`deploy_config.json`)
- Detailed deployment reports (CSV)
- File similarity scoring and color-coded diff viewer

---

## [1.0.0] - 2025-12-09

### Added
- Initial release of PPV Deployment Tool (`deploy_ppv.py`)
- Interactive GUI with tree view for file browsing
- Visual selection checkboxes (☐/☑) for each file
- Smart file comparison using MD5 hashing and difflib
- Similarity scoring (0-100%) for change detection
- Color-coded status indicators
- Side-by-side diff viewer with syntax highlighting
- Automatic backup system with timestamps
- Selective file deployment
- Configurable settings via JSON file

---

## Deployment History

*(Entries below are appended automatically by the deploy tool after each deployment)*


- Interactive GUI with tree view for file browsing
- **Visual selection checkboxes** (☐/☑) for each file
- **Click-to-select** functionality on checkbox column
- **Toggle all visible files** via column header checkbox
- **Change target directory** on the fly with "Change Target" button
- Smart file comparison using MD5 hashing and difflib
- Similarity scoring (0-100%) for change detection
- Color-coded status indicators:
  - Blue: New files
  - Orange: Minor changes
  - Red: Major changes (< 30% similarity)
  - Gray: Identical files
- Side-by-side diff viewer with syntax highlighting
- Dependency analysis for Python imports
- Automatic backup system with timestamps
- Selective file deployment
- Configurable settings via JSON file
- **Advanced filter options**:
  - Text search for file names
  - "Show only files with changes" filter
  - "Show only selected" filter
  - Combine multiple filters
- Bulk selection (select all/deselect all)
- Major change warnings before deployment
- Detailed file information display
- Error handling and reporting
- Spacebar to toggle selection
- Real-time checkbox updates

### Configuration
- Source: `c:\Git\Automation\Automation\PPV`
- Target: `c:\Git\Automation\Automation\S2T\BASELINE\DebugFramework\PPV`
- Backup: `c:\Git\Automation\Automation\DEVTOOLS\backups`
- Similarity threshold: 30%

### Files Included
- `deploy_ppv.py` - Main deployment tool (704 lines)
- `deploy_config.json` - Configuration file
- `launch_deploy.bat` - Quick launcher
- `README.md` - Comprehensive documentation
- `QUICK_START.md` - Quick start guide
- `.gitignore` - Exclude backups from version control
- `CHANGELOG.md` - This file

### Documentation
- Complete user guide with screenshots
- Step-by-step workflow instructions
- Troubleshooting section
- Pro tips and best practices
- Configuration customization guide

---

## Future Enhancements

### Planned Features
- [ ] Command-line interface for automation
- [ ] Configuration profiles for multiple targets
- [ ] Rollback functionality from backups
- [ ] Export comparison reports (HTML/PDF)
- [ ] Git integration for change tracking
- [ ] Schedule automated deployments
- [ ] File exclusion patterns
- [ ] Custom similarity threshold per file type
- [ ] Merge conflict detection
- [ ] Pre-deployment testing hooks

### Ideas Under Consideration
- [ ] Dark mode theme
- [ ] Batch deployment presets
- [ ] Integration with version control
- [ ] Email notifications on deployment
- [ ] Deployment history log
- [ ] Undo last deployment
- [ ] Compare with multiple targets
- [ ] File size change warnings
- [ ] Syntax validation before deployment
- [ ] Integration with CI/CD pipelines

---

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible changes
- MINOR version for new features (backward compatible)
- PATCH version for bug fixes

---

## How to Report Issues

If you encounter bugs or have feature requests:
1. Document the issue with screenshots
2. Include error messages if any
3. Describe steps to reproduce
4. Note your Python version and OS
5. Contact the development team

---

## Credits

**Created by**: GitHub Copilot
**Date**: December 9, 2025
**Python Version**: 3.x
**License**: Internal Use Only

---

## Notes

### Current Deployment Status
Based on initial analysis, the DebugFramework PPV currently excludes:
- `ExperimentBuilder.py`
- `configs/` directory
- Installation scripts
- Requirements file
- Documentation files

This is intentional as these files are development-specific and not needed in the DebugFramework deployment.

### Safety Features
- All deployments create automatic backups
- Major changes trigger confirmation dialogs
- File comparison prevents accidental overwrites
- Error handling ensures no data loss

### Performance
- Fast MD5 hash comparison for identical files
- Efficient difflib algorithm for similarity scoring
- Responsive GUI even with 100+ files
- Background scanning won't freeze the interface

## [20260223_175840] — DMR Deploy — February 23, 2026

### Summary
- **Product:** DMR  
- **Source:** PPV / PPV  
- **Target:** `C:\Git\Automation\S2T\BASELINE_DMR\DebugFramework\PPV`  
- **Files Deployed:** 10  
- **Errors:** 0  
- **Import Replacements:** 0  
- **File Renames:** 0  

### Deployed Files
- `Decoder\decoder_dmr.py`
- `configs\fuses\dmr\cbbsbase.csv`
- `configs\fuses\dmr\cbbstop.csv`
- `gui\PPVFrameworkReport.py`
- `utils\FrameworkFileFix.py`
- `utils\status_bar.py`
- `utils\fusefilegenerator.py`
- `configs\fuses\dmr\imhs.csv`
- `gui\PPVTools.py`
- `gui\fusefileui.py`

---

## [20260223_180001] — DMR Deploy — February 23, 2026

### Summary
- **Product:** DMR  
- **Source:** PPV / PPV  
- **Target:** `C:\Git\Automation\S2T\BASELINE\DebugFramework\PPV`  
- **Files Deployed:** 11  
- **Errors:** 0  
- **Import Replacements:** 0  
- **File Renames:** 0  

### Deployed Files
- `Decoder\decoder_dmr.py`
- `configs\fuses\dmr\cbbsbase.csv`
- `configs\fuses\dmr\cbbstop.csv`
- `parsers\Frameworkparser.py`
- `gui\PPVFrameworkReport.py`
- `utils\FrameworkFileFix.py`
- `utils\status_bar.py`
- `utils\fusefilegenerator.py`
- `configs\fuses\dmr\imhs.csv`
- `gui\PPVTools.py`
- `gui\fusefileui.py`

---

## [20260223_180019] — CWF Deploy — February 23, 2026

### Summary
- **Product:** CWF  
- **Source:** PPV / PPV  
- **Target:** `C:\Git\Automation\S2T\BASELINE\DebugFramework\PPV`  
- **Files Deployed:** 2  
- **Errors:** 0  
- **Import Replacements:** 0  
- **File Renames:** 0  

### Deployed Files
- `configs\fuses\cwf\compute.csv`
- `configs\fuses\cwf\io.csv`

---

## [20260223_180035] — GNR Deploy — February 23, 2026

### Summary
- **Product:** GNR  
- **Source:** PPV / PPV  
- **Target:** `C:\Git\Automation\S2T\BASELINE\DebugFramework\PPV`  
- **Files Deployed:** 2  
- **Errors:** 0  
- **Import Replacements:** 0  
- **File Renames:** 0  

### Deployed Files
- `configs\fuses\gnr\compute.csv`
- `configs\fuses\gnr\io.csv`

---
