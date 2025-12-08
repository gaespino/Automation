# PPV Tools - Installation Guide

## Quick Installation

### Windows

**Option 1: Run the batch file (Recommended)**
```batch
cd c:\Git\Automation\Automation\PPV
install_dependencies.bat
```

**Option 2: Run the Python installer**
```batch
cd c:\Git\Automation\Automation\PPV
python install_dependencies.py
```

**Option 3: Manual installation with pip**
```batch
cd c:\Git\Automation\Automation\PPV
pip install -r requirements.txt
```

### Linux/Mac

**Option 1: Run the Python installer**
```bash
cd /path/to/Automation/PPV
python3 install_dependencies.py
```

**Option 2: Manual installation with pip**
```bash
cd /path/to/Automation/PPV
pip3 install -r requirements.txt
```

---

## Required Dependencies

### External Packages (Need Installation)

| Package | Version | Purpose |
|---------|---------|---------|
| **pandas** | ≥1.3.0 | Data manipulation and analysis |
| **numpy** | ≥1.20.0 | Numerical computing |
| **openpyxl** | ≥3.0.0 | Excel file reading/writing (.xlsx) |
| **xlwings** | ≥0.24.0 | Excel automation and integration |
| **colorama** | ≥0.4.4 | Cross-platform colored terminal output |
| **tabulate** | ≥0.8.9 | Pretty-print tabular data |

### Standard Library (Included with Python)

These packages are included with Python and don't need installation:
- `tkinter` - GUI framework
- `json` - JSON data handling
- `os`, `sys` - System operations
- `re` - Regular expressions
- `zipfile` - ZIP archive handling
- `datetime` - Date and time operations
- `shutil` - File operations
- `subprocess` - Process management
- `http.client` - HTTP protocol
- `collections`, `string`, `pathlib`, `typing`, `uuid`, `argparse`, `csv`, `statistics`

---

## Installation Methods

### Method 1: Automated Batch Script (Windows Only)

The easiest method for Windows users:

```batch
install_dependencies.bat
```

**Features:**
- ✓ Checks Python and pip availability
- ✓ Upgrades pip automatically
- ✓ Installs all packages with progress indicators
- ✓ Verifies successful installation
- ✓ Provides clear error messages

### Method 2: Python Installer Script (Cross-Platform)

Works on Windows, Linux, and Mac:

```bash
python install_dependencies.py
```

**Features:**
- ✓ Cross-platform compatibility
- ✓ Python version checking (requires 3.7+)
- ✓ Automatic pip upgrade
- ✓ Installation verification
- ✓ Detailed error reporting

### Method 3: Requirements File

Standard pip installation:

```bash
pip install -r requirements.txt
```

**When to use:**
- You prefer manual control
- Working in a virtual environment
- Integrating with existing workflows
- CI/CD pipelines

### Method 4: Manual Installation

Install packages individually:

```bash
pip install pandas>=1.3.0
pip install numpy>=1.20.0
pip install openpyxl>=3.0.0
pip install xlwings>=0.24.0
pip install colorama>=0.4.4
pip install tabulate>=0.8.9
```

---

## Virtual Environment (Recommended)

For isolated package management:

### Windows
```batch
# Create virtual environment
python -m venv .venv

# Activate
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Linux/Mac
```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Verification

After installation, verify all packages are working:

```bash
python test_experiment_builder.py
```

Expected output: **5/5 tests passed** ✓

Or manually verify each package:

```python
# Test in Python console
python

>>> import pandas
>>> import numpy
>>> import openpyxl
>>> import xlwings
>>> import colorama
>>> import tabulate
>>> import tkinter
>>> print("All packages imported successfully!")
```

---

## Troubleshooting

### Problem: Python not found
**Solution:**
- Windows: Install from [python.org](https://www.python.org/downloads/)
- Linux: `sudo apt-get install python3` (Ubuntu/Debian)
- Mac: `brew install python3` (with Homebrew)

### Problem: pip not found
**Solution:**
```bash
python -m ensurepip --upgrade
```

### Problem: tkinter not available
**Solution:**
- Windows: Reinstall Python with "tcl/tk" option checked
- Linux: `sudo apt-get install python3-tk`
- Mac: Should be included with Python from python.org

### Problem: xlwings fails to install
**Solution:**
- Ensure Microsoft Excel is installed (required for xlwings)
- On Mac: `pip install xlwings` may require additional setup
- Alternative: PPV Tools can work without xlwings for most features

### Problem: Permission denied
**Solution:**
```bash
# Install for current user only
pip install --user -r requirements.txt

# Or use virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Problem: SSL Certificate error
**Solution:**
```bash
# Trusted host installation
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Problem: Package conflicts
**Solution:**
```bash
# Force reinstall
pip install --force-reinstall -r requirements.txt

# Or create fresh virtual environment
python -m venv .venv_new
```

---

## System Requirements

### Minimum Requirements
- **Python:** 3.7 or higher
- **RAM:** 4 GB (8 GB recommended)
- **Disk Space:** 500 MB for packages
- **OS:** Windows 10+, Linux (Ubuntu 18.04+), macOS 10.14+

### Recommended Requirements
- **Python:** 3.9 or higher
- **RAM:** 8 GB or more
- **Disk Space:** 1 GB free
- **Display:** 1920x1080 or higher for optimal GUI experience

---

## Package Details

### pandas (Data Processing)
- **Purpose:** DataFrame operations, data analysis
- **Used by:** All parsers, analyzers, report builders
- **Documentation:** [pandas.pydata.org](https://pandas.pydata.org/)

### numpy (Numerical Computing)
- **Purpose:** Array operations, mathematical functions
- **Used by:** Data analyzers, statistical calculations
- **Documentation:** [numpy.org](https://numpy.org/)

### openpyxl (Excel File Handling)
- **Purpose:** Read/write Excel files without Excel installation
- **Used by:** Experiment Builder, report generators, parsers
- **Documentation:** [openpyxl.readthedocs.io](https://openpyxl.readthedocs.io/)

### xlwings (Excel Automation)
- **Purpose:** Excel automation with Python (requires Excel)
- **Used by:** PPV Tools Hub, MCA parser
- **Documentation:** [xlwings.org](https://www.xlwings.org/)
- **Note:** Optional for most features, required for Excel automation

### colorama (Terminal Colors)
- **Purpose:** Cross-platform colored terminal output
- **Used by:** Framework parser, console output
- **Documentation:** [pypi.org/project/colorama](https://pypi.org/project/colorama/)

### tabulate (Table Formatting)
- **Purpose:** Pretty-print tabular data
- **Used by:** Framework reports, console displays
- **Documentation:** [pypi.org/project/tabulate](https://pypi.org/project/tabulate/)

---

## Updating Packages

To update all packages to latest versions:

```bash
pip install --upgrade -r requirements.txt
```

To update specific package:

```bash
pip install --upgrade pandas
pip install --upgrade openpyxl
```

To check outdated packages:

```bash
pip list --outdated
```

---

## Uninstallation

To remove all PPV Tools dependencies:

```bash
pip uninstall -y pandas numpy openpyxl xlwings colorama tabulate
```

---

## Support

### Installation Issues
1. Run the verification test: `python test_experiment_builder.py`
2. Check Python version: `python --version` (must be 3.7+)
3. Check pip version: `pip --version`
4. Try virtual environment installation
5. Check system proxy settings if behind corporate firewall

### Package-Specific Issues
- **pandas/numpy:** May require C++ compiler on some systems
- **openpyxl:** Pure Python, should install everywhere
- **xlwings:** Requires Microsoft Excel installation
- **tkinter:** Comes with Python, may need separate install on Linux

### Getting Help
- Review this installation guide
- Check troubleshooting section
- Run diagnostic: `python install_dependencies.py`
- Verify: `python test_experiment_builder.py`
- Contact automation team for assistance

---

## Next Steps

After successful installation:

1. **Verify installation:**
   ```bash
   python test_experiment_builder.py
   ```

2. **Launch PPV Tools Hub:**
   ```bash
   python run.py
   ```

3. **Try Experiment Builder:**
   ```bash
   python run_experiment_builder.py
   ```

4. **Generate Excel template:**
   ```bash
   python gui/create_excel_template.py
   ```

5. **Read documentation:**
   - Main README: `README.md`
   - User Guide: `EXPERIMENT_BUILDER_USER_GUIDE.md`
   - Quick Start: `gui/QUICK_START.md`

---

**PPV Tools** - Comprehensive automation for silicon validation and testing.

*For questions or support, contact the automation team.*
