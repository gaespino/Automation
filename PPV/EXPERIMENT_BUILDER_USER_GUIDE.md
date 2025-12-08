# PPV Experiment Builder - User Guide

## 🎯 What Is This?

The **PPV Experiment Builder** is a new GUI tool that makes it easy to create JSON configuration files for the Debug Framework Control Panel. Instead of manually editing JSON files or Excel spreadsheets, you can now use a visual interface to build, edit, and manage your experiment configurations.

## 🚀 Quick Start

### Launch the Tool

**Option 1: From PPV Tools Hub (Recommended)**
```bash
cd c:\Git\Automation\Automation\PPV
python run.py
```
Then click the **"Experiment Builder"** card (orange color, row 3).

**Option 2: Standalone**
```bash
cd c:\Git\Automation\Automation\PPV
python run_experiment_builder.py
```

### Create Your First Experiment (5 minutes)

1. **Click the `+` button** in the left panel
2. **Fill in basic info:**
   - Test Name: `My_First_Test`
   - Test Mode: `Mesh`
   - Test Type: `Loops`
3. **Go to Test Config tab:**
   - COM Port: `8`
   - IP Address: `192.168.0.2`
   - Test Time: `30`
   - Loops: `10`
4. **Go to Voltage/Freq tab:**
   - Voltage Type: `vbump`
   - Voltage IA: `1.0`
5. **Click "Export to JSON"**
6. **Save the file** - Ready to use in Control Panel!

## 📋 What Can You Do?

### ✨ Key Features

- **Visual Editor**: No more manual JSON editing
- **Import from Excel**: Convert old Excel configurations
- **Import from JSON**: Edit existing configurations
- **Export to JSON**: Generate Control Panel-ready files
- **Validation**: Check for errors before export
- **Preview**: See the JSON before saving
- **Management**: Add, delete, duplicate experiments
- **Search**: Find experiments quickly

### 📊 Interface Overview

The tool has 6 tabs organizing all the fields you need:

1. **Basic Info** - Core settings (Test Name, Mode, Type, etc.)
2. **Test Config** - Hardware & timing (COM, IP, loops, etc.)
3. **Voltage/Freq** - Power settings (voltages, frequencies, sweep params)
4. **Content** - Test content (Linux, Dragon, PYSVConsole)
5. **Advanced** - Debug settings (masks, breakpoints, etc.)
6. **JSON Preview** - Live preview of generated JSON

## 📥 Import from Excel

### Create Excel Template First
```bash
cd c:\Git\Automation\Automation\PPV\gui
python create_excel_template.py
```
This creates `Experiment_Template_Sample.xlsx` with 3 example experiments.

### Excel Format
- **One sheet per experiment** (sheet name = experiment name)
- **Column A**: Field names
- **Column B**: Values

Example:
```
| Field Name    | Value         |
|---------------|---------------|
| Experiment    | Enabled       |
| Test Name     | My_Test       |
| Test Mode     | Mesh          |
| Test Type     | Loops         |
| COM Port      | 8             |
| ...           | ...           |
```

### Import Steps
1. Click **"Import from Excel"** at bottom
2. Select your `.xlsx` file
3. Choose **Merge** (keep existing) or **Replace** (replace all)
4. Done! Experiments appear in left panel

## 💾 Export to JSON

1. **Click "Export to JSON"** at bottom
2. **Choose location** to save file
3. **Use with Control Panel:**
   - Open Debug Framework Control Panel
   - Click "Load Experiments"
   - Select your exported JSON file
   - All experiments load into Control Panel!

## 🛠️ Common Tasks

### Duplicate an Experiment
Perfect for creating variations of a test:
1. Select experiment in left panel
2. Click **📋** (copy button)
3. Edit the copy as needed

### Search Experiments
Type in the search box at top of left panel - filters in real-time.

### Validate Before Export
Click **"Validate All"** button to check for errors:
- Numeric field types
- IP address format
- Required fields
- Value ranges

### Preview JSON
Go to **"JSON Preview"** tab to see exactly what will be exported.
Click **"Copy to Clipboard"** to copy the JSON.

## 📄 Documentation

### Full Documentation
- **README**: `PPV/gui/EXPERIMENT_BUILDER_README.md` - Complete manual
- **Quick Start**: `PPV/gui/QUICK_START.md` - Fast reference guide
- **Implementation**: `PPV/gui/IMPLEMENTATION_SUMMARY.md` - Technical details

### Field Reference
All 50+ fields are documented with:
- Purpose and usage
- Expected format
- Valid values
- Examples

## 🔧 Troubleshooting

### Problem: Import fails
**Check:**
- Excel format: Column A = fields, Column B = values
- Sheet names (no special characters)
- File not open in Excel

### Problem: Validation errors
**Common fixes:**
- COM Port: Must be 0-256
- IP Address: Use format like `192.168.0.2`
- Numeric fields: Remove text
- Required: Test Name, Test Mode, Test Type

### Problem: Can't export JSON
**Check:**
- Write permissions on target folder
- Close any programs with file open
- Try different location

## 📞 Support

1. **Check validation report** - Click "Validate All"
2. **Review documentation** - See README and Quick Start
3. **Check Excel template** - Run `create_excel_template.py`
4. **Test with Control Panel** - Load exported JSON
5. **Contact automation team** - For additional help

## 🎓 Tips for Success

1. **Start Simple**: Create basic experiment first, then add complexity
2. **Use Templates**: Duplicate experiments for variations
3. **Validate Often**: Run "Validate All" before exporting
4. **Preview First**: Check JSON Preview tab
5. **Save Regularly**: Export to JSON to avoid losing work
6. **Name Clearly**: Use descriptive names like `VoltSweep_IA_0.8_1.2`
7. **Search Smart**: Use search to filter large experiment lists

## 📦 What's Included

### Files Created
```
PPV/
├── run_experiment_builder.py          - Standalone launcher
├── test_experiment_builder.py         - Verification tests
└── gui/
    ├── ExperimentBuilder.py           - Main application
    ├── create_excel_template.py       - Template generator
    ├── Experiment_Template_Sample.xlsx - Sample template
    ├── EXPERIMENT_BUILDER_README.md    - Full documentation
    ├── QUICK_START.md                  - Quick reference
    └── IMPLEMENTATION_SUMMARY.md       - Technical summary
```

### Integration
- ✅ Added to PPV Tools Hub (orange card, row 3)
- ✅ Standalone launcher available
- ✅ 100% compatible with Control Panel
- ✅ No external dependencies needed

## ✅ Verification

Run the test suite to verify everything works:
```bash
cd c:\Git\Automation\Automation\PPV
python test_experiment_builder.py
```

Expected output: **5/5 tests passed** ✓

## 🎉 You're Ready!

The PPV Experiment Builder is now installed and ready to use. Launch it from the PPV Tools Hub or standalone, and start creating your experiment configurations!

---

**Need Help?** 
- Full docs: `PPV/gui/EXPERIMENT_BUILDER_README.md`
- Quick start: `PPV/gui/QUICK_START.md`
- Generate template: `python gui/create_excel_template.py`

**Questions?** Contact the automation team.

---

*PPV Experiment Builder - Making experiment configuration simple and efficient.*
