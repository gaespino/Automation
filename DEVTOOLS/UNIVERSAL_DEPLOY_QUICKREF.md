# Universal Deployment Tool - Quick Reference Card

## 🚀 Launch
```bash
launch_deploy_universal.bat
# or
python deploy_universal.py
```

## 📋 Workflow

### 1️⃣ Configure Source
```
Source: [BASELINE] [BASELINE_DMR] [PPV]
Deploy: [DebugFramework] [S2T] [PPV*]
```
*PPV deploy option only available with PPV source

### 2️⃣ Select Target
```
Click: "Select Target..."
Browse to: Product-specific directory
```

### 3️⃣ Load Import Replacements (Optional)
```
Click: "Load CSV..."
Select: import_replacement_gnr.csv (or cwf, dmr)
```

### 4️⃣ Scan Files
```
Click: "Scan Files"
Review: File list, statuses, similarity scores
```

### 5️⃣ Filter & Select
```
☑ Checkbox to select files
🔍 Text filter to search
☐ "Show only changes" to hide identical
☐ "Show only selected" to focus
☐ "Show files with replacements" to filter
```

### 6️⃣ Review Changes
```
Click file: View details and diff
Check: Import replacements that will apply
Verify: Changes are expected
```

### 7️⃣ Deploy
```
Click: "Deploy Selected"
Confirm: Deployment summary
Done: Files deployed with backups
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

### Generate Templates
```bash
# GNR
python generate_import_replacement_csv.py --mode product --product GNR

# CWF
python generate_import_replacement_csv.py --mode product --product CWF

# DMR
python generate_import_replacement_csv.py --mode product --product DMR
```

### CSV Format
```csv
old_import,new_import,description,enabled
from X.Y import,from X.GNRY import,Description,yes
```

### Validate CSV
```bash
python generate_import_replacement_csv.py --mode validate --validate myfile.csv
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
| `generate_import_replacement_csv.py` | CSV generator |
| `import_replacement_gnr.csv` | GNR import rules |
| `import_replacement_cwf.csv` | CWF import rules |
| `import_replacement_dmr.csv` | DMR import rules |
| `UNIVERSAL_DEPLOY_GUIDE.md` | Full documentation |

## 📞 Quick Commands

### Launch Tool
```bash
launch_deploy_universal.bat
```

### Generate New CSV
```bash
python generate_import_replacement_csv.py --mode product --product GNR
```

### Validate Existing CSV
```bash
python generate_import_replacement_csv.py --mode validate --validate myfile.csv
```

### Export Selection
```
UI: Click "Export Selection" → Save as CSV
```

## ⚠️ Remember

- ✅ Always backup before deploying
- ✅ Review major changes carefully
- ✅ Test import replacements first
- ✅ Keep source and target paths correct
- ✅ Use filters to manage large file lists

---

**Version**: 2.0.0 | **Date**: December 9, 2025
