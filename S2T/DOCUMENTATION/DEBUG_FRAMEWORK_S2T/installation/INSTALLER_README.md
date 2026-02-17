# Debug Framework & S2T - Quick Start Installer

**Version:** 1.7.1
**Release Date:** February 16, 2026

---

## 🎯 What This Installer Does

This **standalone** installer replicates the original 2-step installation process:

**Original 2-Step Method:**
1. Run `TeratermEnv.ps1` to set environment variables
2. Import DebugFramework and run `platform_check()` in PythonSV

**New 1-Step Method (This Installer):**
- Single GUI application that does both steps automatically
- No need for manual PythonSV imports during installation
- Standalone - doesn't require existing framework scripts
- Can be delivered to techs for independent system setup

**Note:** The 2-step method is still available and documented in [INSTALLATION_GUIDE.md](../INSTALLATION_GUIDE.md) for troubleshooting or manual configuration.

---

## 🚀 Quick Start (For Techs and Engineers)

### Option 1: Double-Click to Install (Easiest)

1. **Locate the file:** `run_installer.bat`
2. **Double-click** the file
3. **Follow the GUI** to configure and install

### Option 2: Run from Command Line

```powershell
cd C:\Git\Automation\S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T
python debug_framework_installer.py
```

---

## 📋 What You Need

Before running the installer, ensure you have:

- ✅ **Python 3.8+** installed
- ✅ **Windows 10/11** or Windows Server
- ✅ **Administrator privileges** (for environment variables)
- ✅ **Network access** to `\\crcv03a-cifs.cr.intel.com` (for EFI content, optional)

---

## 🖥️ Using the Installer

### Step 1: Launch the Installer

Double-click `run_installer.bat` or run:
```powershell
python debug_framework_installer.py
```

### Step 2: Enter Configuration

In the GUI window, provide:

| Field | Description | Example |
|-------|-------------|---------|
| **COM Port Number** | Your platform's COM port | `8` (for COM8) |
| **Linux IP Address** | Linux boot IP address | `192.168.0.2` |
| **Product** | Select your platform | GNR, CWF, or DMR |
| **EFI Source Path** | (Optional) Local path to EFI content | `D:\EFI_CONTENT` |

### Step 3: Select Options

Choose what to install (recommended defaults):
- ☑ **Install Python dependencies** - pandas, pymongo, xlwings, zeep, etc. (from local requirements.txt)
- ☑ **Configure environment variables** - FrameworkSerial, FrameworkIPAdress, etc.
- ☑ **Configure TeraTerm** - Sets up TERATERM.INI
- ☐ **Transfer EFI content to remote system via SSH** - (Disabled by default)
  - Transfers content to `/run/media/EFI_CONTENT/` on target system
  - Uses FrameworkDefaultUser and FrameworkDefaultPass for authentication
  - Requires SSH/SCP or PuTTY's PSCP installed
  - Browse to select local EFI source path

**Advanced Options:**
- ☑ **Show Advanced TeraTerm Paths** - Configure custom TeraTerm paths
  - TeraTerm Path (default: `C:\teraterm`)
  - SETEO H Path (default: `C:\SETEO H`)
  - INI File Name (default: `TERATERM.INI`)

### Step 4: Click "Start Installation"

- Watch progress in real-time
- Installation takes 2-5 minutes
- Green checkmarks indicate success
- Warnings (orange) are usually non-critical

### Step 5: Restart PythonSV

**IMPORTANT:** If PythonSV was running during installation:
1. Close all PythonSV windows
2. Start PythonSV fresh

### Step 6: Verify

In PythonSV console:

```python
# For GNR
import users.gaespino.DebugFramework.GNRSystemDebug as gdf
gdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')

# For CWF
import users.gaespino.DebugFramework.CWFSystemDebug as cdf
cdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')

# For DMR
import users.gaespino.dev.DebugFramework.SystemDebug as _gdf
_gdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')
```

Expected output:
```
✓ TeraTerm installed and configured
✓ Environment variables set correctly
✓ All required files present
```

---
## 🎨 Interface Features

### Dark Mode
The installer features a modern dark mode interface:
- Reduced eye strain during installation
- Professional appearance
- High contrast for better readability
- Color-coded log messages (green=success, orange=warning, red=error, blue=info)

### SSH Transfer for EFI Content
**NEW:** EFI content can now be transferred directly to the remote system via SSH:
- Content transferred to `/run/media/EFI_CONTENT/` on target
- Uses credentials from environment variables (FrameworkDefaultUser, FrameworkDefaultPass)
- Supports both OpenSSH (scp) and PuTTY (pscp)
- Optional - disabled by default (external drive recommended)

**Prerequisites for SSH Transfer:**
- OpenSSH client or PuTTY installed
- SSH service running on target system
- Network connectivity to target IP
- SSH key authentication recommended (or enter password manually)

---
## ❓ Troubleshooting

### Installer won't start

**Problem:** Double-clicking does nothing or shows error

**Solution:**
- Verify Python is installed: Open CMD and type `python --version`
- If not installed, download from: https://www.python.org/downloads/
- During Python installation, check "Add Python to PATH"

### Missing packages after installation

**Problem:** Import errors in PythonSV

**Solution:**
- Re-run installer with only "Install Python dependencies" checked
- Or manually install: `pip install pandas pymongo xlwings zeep openpyxl`

### Environment variables not working

**Problem:** PythonSV can't find TERATERM_COM_PORT or TERATERM_IP_ADDRESS

**Solution:**
- Close PythonSV completely
- Restart PythonSV (fresh session loads new variables)
- Verify in CMD: `echo %TERATERM_COM_PORT%`

### TeraTerm not found

**Problem:** Installer can't find or configure TeraTerm

**Solution:**
- Install TeraTerm to `C:\teraterm`
- Or ensure it exists at `C:\SETEO_H\teraterm`
- Re-run installer with only "Configure TeraTerm" checked

### Can't access network share

**Problem:** EFI content copy fails

**Solution:**
- Uncheck "Transfer EFI content via SSH" and complete installation
- Manually copy later from:
  ```
  \\crcv03a-cifs.cr.intel.com\mfg_tlo_001\Templates\<GNR|CWF|DMR>\EFI
  ```

### SSH transfer fails

**Problem:** EFI transfer via SSH doesn't work

**Solutions:**
1. **Install SSH client:**
   ```powershell
   # Check if OpenSSH is available
   scp -V
   
   # Or install PuTTY for pscp from: https://www.putty.org/
   ```

2. **Set up SSH key authentication (recommended):**
   ```powershell
   # Generate SSH key
   ssh-keygen -t rsa
   
   # Copy to target
   type $env:USERPROFILE\.ssh\id_rsa.pub | ssh root@<TARGET_IP> "cat >> .ssh/authorized_keys"
   ```

3. **Alternative:** Manually copy EFI content to external drive instead of SSH transfer

### Buttons disappear from interface

**Problem:** Start or Close button not visible

**Solution:**
- This issue was fixed in v1.7.1 with fixed-height button frame
- If it persists, try resizing the window or restarting the installer

---

## 📁 Files in This Directory

| File | Purpose |
|------|---------|
| **run_installer.bat** | Double-click launcher for the installer |
| **debug_framework_installer.py** | Main Python GUI installer |
| **TeratermEnv.ps1** | PowerShell env variable setup (called by installer) |
| **INSTALLATION_GUIDE.md** | Complete installation documentation |
| **README.md** | Full documentation index |
| **THR_DEBUG_FRAMEWORK_USER_MANUAL.md** | Framework usage guide |

---

## 📚 Next Steps After Installation

1. **Learn the basics:** Open [THR_DEBUG_FRAMEWORK_USER_MANUAL.md](THR_DEBUG_FRAMEWORK_USER_MANUAL.md)
2. **Try examples:** Run [THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb](THR_DEBUG_FRAMEWORK_EXAMPLES.ipynb)
3. **Run a test:** Use Quick Test GUIs:
   ```python
   import S2T.SetTesterRegs as s2t
   s2t.MeshQuickTest(GUI=True)
   ```

---

## 🆘 Need Help?

**Contact:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

**Documentation:** See complete docs in this directory:
- Installation Guide
- User Manual
- Quick References
- Example Notebooks

---

**© 2026 Intel Corporation. Intel Confidential.**
