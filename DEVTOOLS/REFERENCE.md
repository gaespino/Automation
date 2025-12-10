# PPV Deployment Tool - Quick Reference Card

## 🚀 Launch
```powershell
python deploy_ppv.py
# or double-click: launch_deploy.bat
```

## ✅ Selection
| Action | How |
|--------|-----|
| Select file | Click checkbox ☐ |
| Deselect file | Click checkbox ☑ |
| Select all visible | Click column header ☑ |
| Select all files | "Select All" button |
| Clear all | "Deselect All" button |
| Toggle highlighted | Spacebar |

## 🔍 Filters
| Filter | Purpose |
|--------|---------|
| Text box | Search file names |
| Show only changes | Hide identical files |
| Show only selected | Review selections |

## 🎨 Status Colors
| Color | Meaning | Similarity |
|-------|---------|------------|
| 🔵 Blue | New file | N/A |
| ⚪ Gray | Identical | 100% |
| 🟢 Green | Minimal changes | 90-99% |
| 🟠 Orange | Minor changes | 30-89% |
| 🔴 Red | Major changes | 0-29% |

## 🎯 Target
- **View**: Top of window shows current target
- **Change**: Click "Change Target..." button
- **Effect**: Clears selections and rescans

## 🔄 Workflow
1. **Filter** → Narrow down files
2. **Select** → Click checkboxes
3. **Review** → Check diff viewer
4. **Dependencies** → Click "View Dependencies"
5. **Deploy** → Click "Deploy Selected"

## ⚡ Power Combos
| Goal | Filters |
|------|---------|
| Changed GUI files | Text: "gui" + Show only changes |
| Review deployment | Show only selected |
| New files only | Show only changes + look for blue |
| All changes | Show only changes |

## 💾 Backup
- **Location**: `DEVTOOLS/backups/{timestamp}/`
- **Format**: `YYYYMMDD_HHMMSS`
- **When**: Before every deployment
- **Restore**: Manual copy from backup

## 🔧 Configuration
Edit `deploy_config.json`:
- `source_base`: Source directory
- `target_base`: Default target
- `similarity_threshold`: Major change threshold (0.3 = 30%)

## ⌨️ Keyboard Shortcuts
| Key | Action |
|-----|--------|
| Spacebar | Toggle selection |
| Arrow keys | Navigate tree |
| Type | Filter files |

## 📞 Help
- `README.md` - Full documentation
- `QUICK_START.md` - Step-by-step guide
- `VISUAL_GUIDE.md` - New features
- `CHANGELOG.md` - Version history

---
**Version**: 1.0.0 | **Date**: Dec 9, 2025
