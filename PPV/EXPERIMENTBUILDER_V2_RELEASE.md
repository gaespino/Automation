# ExperimentBuilder v2.0 - Final Release Notes

## 🎉 Version 2.0 Now Active

ExperimentBuilder v2.0 has **replaced v1.0** as the default experiment configuration tool.

## ✅ Changes Implemented

### 1. **New Fields Added (76 Total)**
- ✅ **Fuse File** - External fuse file to be loaded into the system
- ✅ **Bios File** - BIOS file to be loaded at experiment start

Both fields added to **Advanced Configuration** section with file browse buttons.

### 2. **Product Selection System**
- ✅ **Product dropdown** added to Unit Data panel
- ✅ Three products supported: **GNR**, **CWF**, **DMR**
- ✅ Auto-loads product-specific configuration
- ✅ Updates dropdown options based on selected product

### 3. **Configuration Files Reorganized**
- ✅ **Moved from:** `S2T/BASELINE/DebugFramework/UI/`
- ✅ **Moved to:** `PPV/configs/`
- ✅ Created three product-specific configs:
  - `GNRControlPanelConfig.json` (Granite Rapids)
  - `CWFControlPanelConfig.json` (Clearwater Forest)
  - `DMRControlPanelConfig.json` (Diamond Rapids)

### 4. **File Structure**
```
PPV/
├── gui/
│   ├── ExperimentBuilder.py (v2.0 - ACTIVE)
│   ├── ExperimentBuilder_v1_backup.py (v1.0 - BACKUP)
│   └── ExperimentBuilder_v2.py (v2.0 - ORIGINAL)
└── configs/
    ├── GNRControlPanelConfig.json
    ├── CWFControlPanelConfig.json
    ├── DMRControlPanelConfig.json
    └── README.md
```

## 🎯 Key Features Summary

### Excel-like Interface ✅
- Each tab = One experiment
- Switch between experiments with tabs
- Add/Delete/Duplicate experiments

### Unit Data Panel ✅
- **Product selector** (GNR/CWF/DMR) - NEW!
- Visual ID, Bucket, COM Port, IP Address
- Apply to any experiment with one click

### Templates Panel ✅
- Save current experiment as template
- Load templates into experiments
- Reuse common configurations

### Organized Sections ✅
- 🔹 Basic Information
- 🔹 Test Configuration
- 🔹 Voltage & Frequency
- 🔹 Sweep/Shmoo (Conditional)
- 🔹 Content Selection
- 🔹 Linux Configuration (Conditional)
- 🔹 Dragon Configuration (Conditional)
- 🔹 Advanced Configuration - **NEW FIELDS!**
- 🔹 Merlin Configuration

### Conditional Sections ✅
- **Sweep/Shmoo** - Auto-enabled for Sweep/Shmoo test types
- **Linux** - Auto-enabled when Content = Linux
- **Dragon** - Auto-enabled when Content = Dragon

### Linux Content Lines ✅
- Lines 0-1 shown by default
- Lines 2-9 available in data structure
- Easy to display more if needed

## 🚀 How to Use

### Launch Application
```powershell
python PPV/gui/ExperimentBuilder.py
```

### Select Product
1. In **Unit Data** panel, select product from dropdown
2. Choose: GNR, CWF, or DMR
3. Configuration auto-loads for that product

### Create Experiment
1. Click **"+ New Experiment"**
2. Fill in fields organized by section
3. Test Type/Content changes auto-enable/disable sections
4. Apply Unit Data to populate common fields

### Use Templates
1. Configure an experiment
2. Click **"+ New"** in Templates
3. Name your template
4. Load template into other experiments

### Export
1. Click **"💾 Export to JSON"**
2. All experiments exported
3. Compatible with Control Panel

## 📊 Field Count

- **Total Fields:** 76 (up from 74)
- **New Fields:** 2 (Fuse File, Bios File)
- **Unit Data Fields:** 5 (Product + 4 unit fields)
- **Sections:** 9 organized sections

## 🔄 Migration from v1.0

### Backward Compatibility ✅
- All v1.0 JSON files still work
- Excel import format unchanged
- No breaking changes

### What's Different
| Feature | v1.0 | v2.0 |
|---------|------|------|
| Navigation | Feature tabs | Experiment tabs |
| Config Location | S2T folder | PPV/configs |
| Product Support | Single | Multi (GNR/CWF/DMR) |
| Unit Data | Per-experiment | Shared panel |
| Templates | None | Built-in |
| Fields | 74 | 76 |

## 📁 Product Configurations

### GNR (Granite Rapids)
- **File:** `PPV/configs/GNRControlPanelConfig.json`
- **Default:** Yes
- **Platform:** Server

### CWF (Clearwater Forest)
- **File:** `PPV/configs/CWFControlPanelConfig.json`
- **Platform:** Server

### DMR (Diamond Rapids)
- **File:** `PPV/configs/DMRControlPanelConfig.json`
- **Platform:** Server

## 🛠️ Future Fields (Placeholders Created)

These fields are ready for future functionality:
- **Fuse File** - External fuse configuration
- **Bios File** - BIOS loading at experiment start

Fields are functional in UI and data structure, awaiting Control Panel backend support.

## 📝 Testing Checklist

### Completed ✅
- [x] Launch application
- [x] Product selector dropdown
- [x] Product switching (GNR ↔ CWF ↔ DMR)
- [x] Config loading from PPV/configs
- [x] Create new experiment
- [x] Delete experiment
- [x] Duplicate experiment
- [x] Switch between experiment tabs
- [x] Apply unit data
- [x] Save template
- [x] Load template
- [x] Conditional sections (Sweep/Shmoo)
- [x] Conditional sections (Linux/Dragon)
- [x] Browse buttons for paths
- [x] Fuse File field visible
- [x] Bios File field visible
- [x] Import from Excel
- [x] Import from JSON
- [x] Export to JSON
- [x] Validation

## 🎯 Quick Reference

### Launch
```powershell
python PPV/gui/ExperimentBuilder.py
```

### Files
- **Main:** `PPV/gui/ExperimentBuilder.py`
- **Configs:** `PPV/configs/{PRODUCT}ControlPanelConfig.json`
- **Backup:** `PPV/gui/ExperimentBuilder_v1_backup.py`

### Products
- **GNR** - Granite Rapids (Default)
- **CWF** - Clearwater Forest
- **DMR** - Diamond Rapids

### New Fields Location
- **Section:** Advanced Configuration
- **Fields:** Fuse File, Bios File
- **Type:** String with browse buttons

## 📚 Documentation

- **Main Guide:** `PPV/EXPERIMENTBUILDER_V2_REDESIGN.md`
- **Config README:** `PPV/configs/README.md`
- **Field List:** `PPV/FIELD_UPDATE_SUMMARY.md`
- **Installation:** `PPV/INSTALLATION.md`

## 🔧 Support

### Common Issues

**Q: Product dropdown not changing options?**  
A: Options update for new experiments. Existing experiments keep their original config.

**Q: Can't find config files?**  
A: They're in `PPV/configs/` - no longer in S2T folder.

**Q: Missing v1.0?**  
A: Backed up as `ExperimentBuilder_v1_backup.py`

**Q: New fields not in export?**  
A: Check field is populated. Empty fields export as empty strings.

## 🎉 Summary

ExperimentBuilder v2.0 is now the default with:
- ✅ Excel-like interface (tabs = experiments)
- ✅ Product selection (GNR/CWF/DMR)
- ✅ Unit Data panel (shared config)
- ✅ Templates system (save/reuse)
- ✅ 76 fields (added Fuse File, Bios File)
- ✅ Config files in PPV/configs
- ✅ Conditional sections
- ✅ 100% backward compatible

**Status:** ✅ PRODUCTION READY  
**Replaces:** v1.0 (backed up)  
**Version:** 2.0  
**Released:** December 8, 2024

---

**Maintained By:** Automation Team  
**Contact:** gaespino
