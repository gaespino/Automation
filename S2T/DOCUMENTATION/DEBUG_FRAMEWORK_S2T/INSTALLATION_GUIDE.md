# Debug Framework & S2T - Complete Installation Guide

**Version:** 1.7.1
**Release Date:** February 17, 2026
**Organization:** Intel Corporation - Test & Validation
**Classification:** Intel Confidential
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)
**Products:** GNR, CWF, DMR
**Repository:** `c:\Git\Automation\S2T\`

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Automated Installation (Recommended)](#automated-installation-recommended)
4. [Manual Installation](#manual-installation)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Additional Resources](#additional-resources)

---

## Overview

This guide covers the complete installation process for the Debug Framework and S2T tools. The latest version (1.7+) includes automated configuration with environment variables and system validation tools.

### What Gets Installed

- ✅ Environment variables for TeraTerm configuration
- ✅ Python dependencies (pandas, pymongo, xlwings, zeep, etc.)
- ✅ TeraTerm configuration files
- ✅ EFI test content and setup scripts
- ✅ Framework validation and system checks

### New Features in Version 1.7+

- **Encrypted Credentials** - 🔐 AES-256 encrypted password storage (credentials.enc) - **NEW!**
- **Automatic Environment Variables** - No manual TTL modifications needed
- **System Configuration Validation** - Built-in checks for TeraTerm and environment
- **One-Click Installation** - GUI installer with visual progress
- **Enhanced Error Reporting** - Clear diagnostics for missing dependencies
- **Dark Mode UI** - Professional dark theme for reduced eye strain
- **SSH/SCP Transfer** - Direct EFI content transfer to Linux-booted units
- **Product-Based Defaults** - Auto-populated EFI paths based on product selection
- **Verbose Logging** - Complete console output for all operations

---

## Prerequisites

### Required Software

- **Python 3.8+** with PythonSV
- **Windows 10/11** or Windows Server
- **Git** (for repository updates)
- **TeraTerm** (will be configured automatically)
- **Microsoft Excel** (for xlwings functionality)

### Required Hardware

- Serial COM port connection to target unit
- Network connectivity to target unit (for Linux boot)
- ITP connection
- **For SSH Transfer:** Unit must be booted to Linux with SSH server running

### Required Access

- Access to `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\`
- GitHub access to Intel-restricted repositories
- PythonSV installation and licensing

---

## Installation (One-Click GUI Installer)

### 🔐 RECOMMENDED: Use Encrypted Credentials (New in v1.7.1)

**For easier deployment**, use encrypted credentials file instead of manual password entry:

1. **Administrators**: Create `credentials.enc` file once:
   ```powershell
   cd C:\Git\Automation\S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T\installation
   pip install cryptography
   python credentials_manager.py create
   ```

2. **Distribute** `credentials.enc` and `credentials.key` to end users (secure channels only)

3. **End users**: Place both files in `installation/` folder before running installer

4. **Result**: Installer automatically loads credentials - no manual entry needed! ✅

**Benefits:**
- ✅ No password prompts during installation
- ✅ AES-256 encrypted security
- ✅ Easy distribution to multiple users
- ✅ Never committed to Git

📖 **Full documentation:** [installation/CREDENTIALS_SETUP.md](installation/CREDENTIALS_SETUP.md)

---

### Step 1: Update Git Repository

```powershell
cd C:\Git\Automation\S2T
git pull origin main
```

**Important:** Ensure you are on the latest version (1.7+) before proceeding.

### Step 2: Run Python GUI Installer

```powershell
cd C:\Git\Automation\S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T
python installation/debug_framework_installer.py
```

**Or** double-click `installation/debug_framework_installer.py` from Windows Explorer (or use `installation/run_installer.bat`).

### Step 3: Configure Settings

The GUI installer will open with the following options:

**Required Configuration:**
- **COM Port Number** - Enter your platform's COM port (e.g., 8 for COM8)
- **Linux IP Address** - Enter the Linux boot IP (e.g., 192.168.0.2)
- **Product** - Select GNR, CWF, or DMR (auto-populates EFI source path)

**SSH Transfer Configuration** (Optional - for direct Linux transfer):
- **Enable SSH Transfer** - Check to enable direct transfer to Linux-booted unit
- **EFI Source Path** - Network path to EFI content (auto-populated based on product)
  - GNR: `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\GNR\EFI`
  - CWF: `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\CWF\EFI`
  - DMR: `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\DMR\EFI`
- **SSH Username** - Linux username (default: root)
- **SSH Password** - Linux password (optional - see note below)
- **Remote Path** - Linux destination path (default: /run/media/EFI_CONTENT/)

**Important SSH Notes:**
- Unit **MUST be booted to Linux** before starting SSH transfer
- SSH server must be running on target unit
- If no password provided, you'll be prompted in the **CONSOLE window**
- A popup will alert you when console password input is needed
- Install `sshpass` for automatic password authentication (optional)
- Alternatively, set up SSH key authentication for passwordless transfers

**Optional Configuration:**
- **Test Suite Path** - Path to your Test Suite root (for local EFI content copy)

**Installation Options** (all enabled by default):
- ✅ Install Python dependencies
- ✅ Configure environment variables
- ✅ Configure TeraTerm
- □ Transfer EFI content via SSH (optional - requires Linux boot)
- □ Copy EFI content locally (legacy method)

### Step 4: Click "Start Installation"

The installer will automatically:
1. ✓ Check Python installation
2. ✓ Install all required packages (pandas, pymongo, xlwings, zeep, etc.)
3. ✓ Configure environment variables (TERATERM_COM_PORT, TERATERM_IP_ADDRESS)
4. ✓ Configure TeraTerm INI file
5. ✓ Copy EFI content to Test Suite (if path provided)
6. ✓ Validate installation

Progress is shown in real-time in the installer window.

### Step 5: Restart PythonSV

**Critical:** If PythonSV was open during installation, close and restart it to refresh environment variables.

### Step 6: Verify Installation

```python
# In PythonSV console - GNR Example
import users.gaespino.DebugFramework.GNRSystemDebug as gdf
gdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')

# CWF Example
import users.gaespino.DebugFramework.CWFSystemDebug as cdf
cdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')

# DMR Example (Development)
import users.gaespino.dev.DebugFramework.SystemDebug as _gdf
_gdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')
```

**Expected Output:**
```
✓ TeraTerm installed and configured
✓ Environment variables set correctly
✓ COM port: 8
✓ IP address: 192.168.0.2
✓ All required files present
```

---

## GUI Installer Features

The Python GUI installer provides:

### Visual Interface
- **Dark Mode UI** - Professional dark theme (#1e1e1e background, #007acc accents)
- **Real-time Progress** - See installation steps as they happen
- **Configuration Options** - Enable/disable specific installation steps
- **Color-coded Logging** - Easy identification of errors (red), warnings (yellow), success (green)
- **Progress Bar** - Visual feedback during long operations
- **Password Toggle** - Show/hide password for secure entry
- **Popup Alerts** - Message boxes for important notifications (e.g., console password prompts)
- **Verbose Console Logging** - All commands and outputs logged to console window

### Automated Steps

1. **Python Check** - Verifies Python 3.8+ is installed
2. **Dependency Installation** - Installs all required packages:
   - pandas, numpy (data processing)
   - openpyxl, xlwings (Excel operations)
   - pymongo (database)
   - colorama, tabulate (CLI formatting)
   - zeep (SOAP operations)
   - pytz, psutil, lxml (utilities)

3. **Environment Configuration** - Sets system variables:
   - `TERATERM_COM_PORT` - Your COM port number
   - `TERATERM_IP_ADDRESS` - Linux boot IP address

4. **TeraTerm Setup** - Configures TeraTerm INI file:
   - COM port settings
   - Baud rate (115200)
   - Parity, data bits, stop bits
   - Flow control
   - Framework variables

5. **EFI Content Transfer** (Optional) - Two methods available:
   
   **Method 1: SSH Transfer (Recommended for Linux-booted units)**
   - Direct transfer to Linux target via SSH/SCP
   - Requires unit to be booted to Linux with SSH server running
   - Copies all EFI content from network source to `/run/media/EFI_CONTENT/`
   - Automatically copies `startup_linux.nsh` and `startup_efi.nsh` to base path
   - Supports password authentication (sshpass) or interactive prompt
   - Uses OpenSSH `scp` or PuTTY `pscp` (whichever is available)
   - **Important:** Unit MUST be in Linux before enabling this option
   
   **Method 2: Local Copy (Legacy)**
   - Copies EFI content to local Test Suite directory
   - runregression.nsh, ulx utilities, setup scripts
   - startup_efi.nsh and startup_linux.nsh

6. **Validation** - Verifies installation:
   - Package imports
   - Environment variables
   - TeraTerm configuration
   - File accessibility

### Smart Configuration

The installer intelligently handles:
- **Missing TeraTerm** - Copies from C:\SETEO_H if not found
- **Failed PowerShell** - Falls back to manual setx commands
- **Product-Based Paths** - Auto-populates EFI source path when product selected
- **SSH Password Management** - Secure password entry with show/hide toggle
- **Console Password Prompts** - Popup alerts when password input needed in console
- **sshpass Detection** - Uses sshpass if available, otherwise prompts interactively
- **Startup File Copying** - Automatically copies startup scripts to remote base path
- **Network Issues** - Skips EFI transfer if network unavailable (non-critical)
- **Partial Installation** - Can retry failed steps without reinstalling everything

---

## Alternative: Manual 2-Step Installation

For users who prefer manual configuration or need to troubleshoot installation issues, the original 2-step method is still available:

### Overview

The automated GUI installer replicates this 2-step process. Understanding these manual steps can help with troubleshooting.

**Step 1:** Run `TeratermEnv.ps1` to set environment variables  
**Step 2:** Import DebugFramework and run `platform_check()` in PythonSV

### Step 1: Set Environment Variables with TeratermEnv.ps1

```powershell
cd C:\Git\Automation\S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T\installation
.\TeratermEnv.ps1 -com 8 -ip 192.168.0.2
```

**What this does:**
- Sets `FrameworkSerial` (COM port)
- Sets `FrameworkIPAdress` (IP address)
- Sets `FrameworkDefaultPass` and `FrameworkDefaultUser`
- Sets `DANTA_DB_PASSWORD`

**Variables set (User level):**
```powershell
FrameworkSerial = <your_com_port>
FrameworkIPAdress = <your_ip_address>
FrameworkDefaultPass = password
FrameworkDefaultUser = root
DANTA_DB_PASSWORD = Keepingtrack2
```

### Step 2: Configure TeraTerm with platform_check()

**Restart PythonSV** to load the environment variables, then run:

```python
# For GNR
import users.gaespino.DebugFramework.GNRSystemDebug as gdf
gdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')

# For CWF
import users.gaespino.DebugFramework.CWFSystemDebug as cdf
cdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')

# For DMR
import users.gaespino.dev.DebugFramework.SystemDebug as gdf
gdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')
```

**What platform_check() does:**
- Checks if TeraTerm is installed at `C:\teraterm`
- If not found, copies from `C:\SETEO H\teraterm`
- Configures `TERATERM.INI` with COM port settings:
  - ComPort, BaudRate, Parity, DataBit, StopBit, FlowCtrl
  - DelayPerChar, DelayPerLine
- Validates environment variables match configuration
- Reports success or errors

### Manual Alternative: Direct Variable Setting

If PowerShell script fails, set variables manually:

```powershell
# Set environment variables (User level)
setx FrameworkSerial "8"
setx FrameworkIPAdress "192.168.0.2"
setx FrameworkDefaultPass "password"
setx FrameworkDefaultUser "root"
setx DANTA_DB_PASSWORD "Keepingtrack2"
```

**Then restart PythonSV and run platform_check().**

### Why Use Manual Method?

- **Troubleshooting:** Isolate which step is failing
- **Custom Configuration:** Need different TeraTerm paths
- **Learning:** Understand what the installer does
- **Automation:** Script your own deployment process
- **Debugging:** Step through configuration manually

### TeraTerm Path Configuration

The automated installer uses these defaults (from `SerialConnection.py`):

```python
TERATERM_PATH = r'C:\teraterm'
TERATERM_RVP_PATH = r'C:\SETEO H'
TERATERM_INI_FILE = 'TERATERM.INI'
```

If your installation uses different paths:
1. Enable "Show Advanced TeraTerm Paths" in the GUI installer, OR
2. Modify `SerialConnection.py` in your framework installation, OR
3. Manually edit `TERATERM.INI` after installation

---

## Verification

The installer automatically validates installation, but you can manually verify:

### Check Python Packages

```powershell
pip list | Select-String -Pattern "pandas|pymongo|xlwings|zeep|openpyxl"
```

### Check Environment Variables

```powershell
echo $env:TERATERM_COM_PORT
echo $env:TERATERM_IP_ADDRESS
```

### Test Framework Import

```python
# Import framework modules
import users.gaespino.DebugFramework.GNRSystemDebug as gdf
import users.THR.PythonScripts.thr.S2T.dpmChecks as dpm
print("Framework loaded successfully!")
```

---

## Troubleshooting

### Issue: Installer won't start

**Cause:** Python not in PATH or tkinter not installed.

**Solution:**
```powershell
# Verify Python
python --version

# Test tkinter
python -m tkinter

# If tkinter fails, reinstall Python with tcl/tk support
```

### Issue: Environment Variables Not Loading in PythonSV

**Cause:** PythonSV caches environment variables on startup.

**Solution:** Close PythonSV completely and restart it.

```powershell
# Force close all Python processes
Get-Process python* | Stop-Process -Force

# Restart PythonSV
```

### Issue: pip install fails for xlwings

**Cause:** xlwings requires Microsoft Excel to be installed.

**Solution:**
1. Verify Excel is installed
2. Run installer as Administrator
3. Or install manually: `pip install xlwings --user`

### Issue: Cannot access network share for EFI content

**Cause:** Network drive not mapped or no permissions.

**Solution:**
- Uncheck "Copy EFI content" in installer
- Manually copy EFI content later from:
  ```
  \\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\<PRODUCT>\EFI
  ```

### Issue: TeraTerm not found

**Cause:** TeraTerm not in C:\teraterm or C:\SETEO_H.

**Solution:**
1. Install TeraTerm to C:\teraterm manually
2. Configure COM port in TERATERM.INI:
   ```ini
   ComPort=8
   BaudRate=115200
   ```

### Issue: Installer shows warnings but completes

**Explanation:** Some warnings are non-critical:
- Missing EFI content (if no network access)
- PowerShell script issues (falls back to setx)
- Optional packages (framework will still function)

**Action:** Review warnings in installer log. Installation can proceed if validation passes.

### Issue: SSH Transfer fails - "Connection refused"

**Cause:** Unit is not booted to Linux or SSH server is not running.

**Solution:**
1. **Boot unit to Linux** - SSH transfer only works with Linux-booted units
2. Verify SSH server is running on target:
   ```bash
   # On target Linux unit
   systemctl status sshd
   ```
3. Test SSH connection manually:
   ```powershell
   ssh root@192.168.0.2
   ```
4. If SSH fails, check network connectivity:
   ```powershell
   ping 192.168.0.2
   ```

### Issue: SSH Transfer prompts for password in console

**Cause:** sshpass is not installed or no password was provided in GUI.

**Solution:**
- **Expected behavior:** A popup message box will alert you to check the console
- Enter password in the **CONSOLE window** (black command prompt), not the GUI
- The installer will wait for password input before continuing

**To avoid console prompts (optional):**
- Install sshpass: Download from [sshpass official site](https://sourceforge.net/projects/sshpass/)
- Or set up SSH key authentication:
  ```powershell
  # Generate SSH key (if not exists)
  ssh-keygen -t rsa
  
  # Copy key to target
  ssh-copy-id root@192.168.0.2
  ```

### Issue: EFI Source Path is blank

**Cause:** No product selected in dropdown.

**Solution:**
1. Select a product (GNR, CWF, or DMR) from the dropdown
2. EFI source path will auto-populate:
   - GNR: `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\GNR\EFI`
   - CWF: `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\CWF\EFI`
   - DMR: `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\DMR\EFI`
3. You can manually edit or browse for a different path if needed

### Issue: SSH Transfer completes but startup files not copied

**Cause:** startup_linux.nsh or startup_efi.nsh not found in EFI source.

**Solution:**
- Non-critical warning - main EFI content was transferred successfully
- Verify files exist in source path:
  ```
  \\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\<PRODUCT>\EFI\startup_linux.nsh
  \\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\<PRODUCT>\EFI\startup_efi.nsh
  ```
- Manually copy startup files if needed:
  ```bash
  # On Linux target
  cp /path/to/startup_linux.nsh /run/media/EFI_CONTENT/
  cp /path/to/startup_efi.nsh /run/media/EFI_CONTENT/
  ```

### Issue: GUI buttons (Start/Close) not visible

**Cause:** Window size too small or display scaling issues.

**Solution:**
- Fixed in version 1.7.1 (window size increased to 900x850)
- Try maximizing the window
- Check display scaling settings (should work with 100%, 125%, 150%)

---

## Additional Resources

### Documentation Files

- **[installation/CREDENTIALS_SETUP.md](installation/CREDENTIALS_SETUP.md)** - **Secure credential management guide** (📌 Read this first!)
- **[THR_DEBUG_FRAMEWORK_USER_MANUAL.md](THR_DEBUG_FRAMEWORK_USER_MANUAL.md)** - Complete framework documentation
- **[FUSE_FILE_QUICK_REFERENCE.md](FUSE_FILE_QUICK_REFERENCE.md)** - Fuse file format guide
- **[THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md](THR_DEBUG_FRAMEWORK_FILE_NAMING_AND_IMPORTS.md)** - File naming conventions
- **[THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb)** - Interactive examples
- **[THR_S2T_EXAMPLES.ipynb](THR_S2T_EXAMPLES.ipynb)** - S2T usage examples

### Network Locations

- **Configuration Files:** `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\ConfigFiles\`
- **GNR Templates:** `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\GNR\`
- **CWF Templates:** `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\CWF\`
- **DMR Templates:** `\\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\DMR\`

### Support

**Primary Maintainer:**
- Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

**Repository Issues:**
- Open issues on GitHub project pages

**Internal Documentation:**
- Confluence: [Search "BASELINE Framework"]
- Wiki: [Search "S2T Debug Framework"]

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | February 16, 2026 | Initial installation guide |
| 1.7 | February 16, 2026 | Added automated installation script |
| - | - | Added MDT tools and fuse dump documentation |
| - | - | Updated for version 1.7 features |
| 1.7.1 | February 17, 2026 | Added SSH/SCP transfer for Linux-booted units |
| - | - | Added dark mode UI with professional styling |
| - | - | Added product-based default EFI paths (GNR/CWF/DMR) |
| - | - | Added automatic startup file copying (startup_linux.nsh, startup_efi.nsh) |
| - | - | Added password show/hide toggle and popup alerts for console prompts |
| - | - | Added verbose console logging for all operations |
| - | - | Fixed button visibility issues (increased window to 900x850) |
| - | - | Removed hardcoded default passwords for Git security |
| - | - | **Added encrypted credentials system (credentials.enc) with AES-256 encryption** |
| - | - | Added credentials_manager.py for secure password management |
| - | - | Updated .gitignore to exclude all credential files (.enc, .key) |
| - | - | Added cryptography library to requirements.txt |

---

**End of Installation Guide**
