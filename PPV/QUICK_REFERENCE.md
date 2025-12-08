# PPV Tools - Quick Reference Card

## 🚀 Installation

```bash
# Windows (Automated)
install_dependencies.bat

# Cross-Platform
python install_dependencies.py

# Manual
pip install -r requirements.txt
```

## 📦 Required Packages

| Package | Version | Purpose |
|---------|---------|---------|
| pandas | ≥1.3.0 | Data processing |
| numpy | ≥1.20.0 | Numerical computing |
| openpyxl | ≥3.0.0 | Excel files |
| xlwings | ≥0.24.0 | Excel automation |
| colorama | ≥0.4.4 | Terminal colors |
| tabulate | ≥0.8.9 | Table formatting |

## 🎯 Launching Tools

```bash
# PPV Tools Hub (All Tools)
python run.py

# Experiment Builder (Standalone)
python run_experiment_builder.py

# Generate Excel Template
python gui/create_excel_template.py

# Run Verification Tests
python test_experiment_builder.py
```

## 🛠️ Common Tasks

### Create New Experiment
1. Launch Experiment Builder
2. Click `+` button
3. Fill in fields across tabs
4. Export to JSON

### Import from Excel
1. Generate template: `python gui/create_excel_template.py`
2. Edit template with your data
3. Open Experiment Builder
4. Click "Import from Excel"

### Export to Control Panel
1. Click "Export to JSON"
2. Open Debug Framework Control Panel
3. Click "Load Experiments"
4. Select your JSON file

## 📁 File Structure

```
PPV/
├── run.py                           - Main launcher
├── run_experiment_builder.py        - Experiment Builder
├── install_dependencies.bat         - Windows installer
├── install_dependencies.py          - Cross-platform installer
├── requirements.txt                 - Package list
├── test_experiment_builder.py       - Tests
├── README.md                        - Main docs
├── INSTALLATION.md                  - Install guide
└── gui/
    ├── ExperimentBuilder.py         - Main app
    ├── PPVTools.py                  - Tools hub
    ├── create_excel_template.py     - Template gen
    └── *.md                         - Documentation
```

## ✅ Verification

```bash
# Run all tests (should show 5/5 passed)
python test_experiment_builder.py

# Verify packages manually
python -c "import pandas, numpy, openpyxl, xlwings, colorama, tabulate; print('✓ All OK')"
```

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Python not found | Install from python.org |
| pip not found | `python -m ensurepip` |
| Permission denied | Use `--user` flag or venv |
| tkinter missing | Reinstall Python with tk/tcl |
| xlwings fails | Ensure Excel is installed |

## 📖 Documentation

- **README.md** - Overview and features
- **INSTALLATION.md** - Detailed install guide
- **EXPERIMENT_BUILDER_USER_GUIDE.md** - User manual
- **gui/QUICK_START.md** - 5-minute guide
- **gui/EXPERIMENT_BUILDER_README.md** - Full reference

## 🆘 Getting Help

1. Check documentation in `gui/` folder
2. Run verification: `python test_experiment_builder.py`
3. Review INSTALLATION.md troubleshooting section
4. Contact automation team

## 🎓 Example Workflow

```bash
# 1. Install dependencies
python install_dependencies.py

# 2. Verify installation
python test_experiment_builder.py

# 3. Generate template
python gui/create_excel_template.py

# 4. Launch Experiment Builder
python run_experiment_builder.py

# 5. Create experiments and export JSON

# 6. Use JSON in Control Panel
```

---

**Version:** 1.0 | **Date:** December 2024 | **Platform:** Windows/Linux/Mac
