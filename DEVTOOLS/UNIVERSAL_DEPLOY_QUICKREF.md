# Universal Deployment Tool - Quick Reference Card

## 🚀 Launch
```bash
launch_deploy_universal.bat
# or
python deploy_universal.py
```

## 📋 Tab 1 — Deploy

### 1️⃣ Configure Source
```
Source: [BASELINE] [BASELINE_DMR] [PPV]
Deploy: [DebugFramework] [S2T] [PPV*]
Product: [GNR] [CWF] [DMR]
```
*PPV deploy only available with PPV source

### 2️⃣ Select Target
```
Click: "Select Target..."
Browse to: Product-specific directory
```

### 3️⃣ Load Import Replacements (Optional)
```
Click: "Load CSV..."  or  "Generate..."
Select: import_replacement_gnr.csv (or cwf, dmr)
```

### 4️⃣ Load File Rename CSV (Optional)
```
Click: "Load CSV..."  or  "Generate..."
Select: file_rename_gnr.csv (or cwf, dmr)
```

### 5️⃣ Scan Files
```
Click: "Scan Files"
Review: File list, statuses, similarity scores
```

### 6️⃣ Filter & Select
```
☑ Checkbox to select files
🔍 Text filter to search
☐ "Show only changes" to hide identical
☐ "Show only selected" to focus
☐ "Show files with replacements" to filter
```

### 7️⃣ Review Changes
```
Click file: View details and diff
Check: Import replacements that will apply
Verify: Changes are expected
```

### 8️⃣ Deploy
```
Click: "Deploy Selected"
Confirm: Deployment summary
Done: Files deployed with backups + changelog updated
```

## 📊 Tab 2 — Reports & Changelog

```
View history: Scrollable deployment list
Open report: Click any entry -> opens CSV in default app
View changelog: "View Changelog" button -> CHANGELOG.md
```

Every deployment auto-appends to `deployment_changelog.json` and `CHANGELOG.md`.

## 📄 Tab 3 — Release Notes

```
Generate: From deployment history
Save:     Draft Markdown file
Export:   HTML version
PR:       Create draft PR via gh CLI
```

## 🔍 Validation Agent

```
Button: "Validate & Review..."
Runs: deploy_agent.py in a streaming log window
Flags: --validate  --lint  --test --quick  --pr --draft
```

## 🎯 Common Tasks

### Deploy BASELINE to GNR
1. Source: `BASELINE`
2. Deploy: `DebugFramework`
3. Target: `.../BASELINE_GNR/DebugFramework`
4. CSV: `import_replacement_gnr.csv`
5. Scan → Select → Deploy

### Deploy Only S2T Files
1. Source: `BASELINE`
2. Deploy: `S2T`
3. Target: `.../ProductName/S2T`
4. CSV: Product-specific CSV
5. Scan → Select → Deploy

### Deploy DMR Variant
1. Source: `BASELINE_DMR`
2. Deploy: `DebugFramework` or `S2T`
3. Target: DMR directory
4. CSV: `import_replacement_dmr.csv`
5. Scan → Select → Deploy

### Deploy PPV Tools
1. Source: `PPV`
2. Deploy: `PPV` (auto-selected)
3. Target: Product PPV location
4. CSV: Optional
5. Scan → Select → Deploy

## 🔄 Import Replacement CSV

### Generate from UI
```
In Tab 1, click "Generate..." next to Import Replacement CSV
Select product -> customize -> Generate
CSV is created and loaded automatically
```

### Or load an existing CSV
```
Click "Load CSV..." and select import_replacement_<product>.csv
```

### CSV Format
```csv
old_import,new_import,description,enabled
from X.Y import,from X.GNRY import,Description,yes
```

## 🎨 Status Colors

| Color | Status | Similarity | Action |
|-------|--------|------------|--------|
| 🔵 Blue | New File | - | Review before deploy |
| ⚫ Gray | Identical | 100% | Safe to skip |
| 🟠 Orange | Minor Changes | 30-90% | Review changes |
| 🔴 Red | Major Changes | <30% | ⚠️ Careful review |

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Toggle selected file |
| `↑`/`↓` | Navigate files |
| `Enter` | View file details |

## 📊 File List Columns

| Column | Description |
|--------|-------------|
| ☑ | Selection checkbox (click to toggle) |
| Status | Comparison status |
| Similar | Similarity percentage |
| Replacements | Number of import rules |

## 🔍 Filters

### Text Filter
```
Type: filename or path
Example: "dpm" shows all files with "dpm"
```

### Smart Filters
- **Show only changes**: Hides identical files
- **Show only selected**: Shows checked files only
- **Show files with replacements**: Shows files with import rules

### Combine Filters
```
Text: "System"
☑ Show only changes
☑ Show files with replacements
Result: Changed files named "System*" with import rules
```

## 🛡️ Safety Features

### Automatic Backups
```
Location: DEVTOOLS/backups/YYYYMMDD_HHMMSS/
Format: Original directory structure preserved
```

### Major Changes Warning
Files with <30% similarity trigger confirmation dialog

### Deployment Summary
Shows:
- Number of files
- Import replacement count
- Backup location
- Warnings if any

## 🐛 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Source not found | Check source selection matches structure |
| Can't select target | Ensure directory exists and has write access |
| No files shown | Click "Scan Files" after configuration |
| CSV not working | Validate CSV format and column names |
| Major changes alert | Review diff carefully before deploying |

## 📁 File Structure Expected

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

## 💡 Pro Tips

1. **Test First**: Deploy to test directory first
2. **Small Batches**: Deploy a few files at a time
3. **Review Diffs**: Always check changes before deploying
4. **Keep CSVs Updated**: Maintain replacement rules as code evolves
5. **Use Filters**: Combine filters to focus on specific files
6. **Export Selection**: Save selection list for documentation
7. **Validate CSVs**: Always validate before using new CSV files

## 🔗 Related Files

| File | Purpose |
|------|---------|
| `deploy_universal.py` | Main deployment tool |
| `deploy_agent.py` | Validation + PR agent |
| `import_replacement_gnr.csv` | GNR import rules |
| `import_replacement_cwf.csv` | CWF import rules |
| `import_replacement_dmr.csv` | DMR import rules |
| `file_rename_gnr.csv` | GNR file rename rules |
| `file_rename_cwf.csv` | CWF file rename rules |
| `file_rename_dmr.csv` | DMR file rename rules |
| `UNIVERSAL_DEPLOY_GUIDE.md` | Full documentation |

## 📞 Quick Commands

### Launch Tool
```bash
launch_deploy_universal.bat
```

### Run Validation Agent (CLI)
```bash
python deploy_agent.py --validate --lint --test --quick --product GNR --target DEVTOOLS
```

### Create Draft PR
```bash
python deploy_agent.py --pr --draft --title "Release v1.8.0"
```

### Export Selection (from UI)
```
Click "Export Selection" -> Save as CSV
```

## ⚠️ Remember

- ✅ Always backup before deploying
- ✅ Review major changes carefully
- ✅ Test import replacements first
- ✅ Keep source and target paths correct
- ✅ Use filters to manage large file lists

---

**Version**: 3.0.0 | **Date**: February 23, 2026
