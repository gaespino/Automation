# Debug Framework & S2T - Installation Package

**Version:** 1.7.1
**Date:** February 17, 2026
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

---

## 📦 Package Contents

```
installation/
├── run_installer.bat          ⭐ DOUBLE-CLICK TO START (Windows)
├── run_installer.ps1          ⭐ PowerShell launcher (alternative)
├── README.md                  📖 This file
│
├── keys/                      🔐 Encrypted credentials (distributed with package)
│   ├── credentials.enc               (Encrypted credential file)
│   └── credentials.key               (Encryption key)
│
├── scripts/                   📜 Installation scripts
│   ├── debug_framework_installer.py    (Main GUI installer)
│   ├── credentials_manager.py          (Credential encryption utility)
│   ├── create_credentials.py           (Credential creation helper)
│   └── TeratermEnv.ps1                 (Environment variable setup)
│
├── docs/                      📄 Documentation
│   ├── CREDENTIALS_SETUP.md            (Credential management guide)
│   ├── README_CREDENTIALS.md           (Quick credential reference)
│   └── credentials.template.json       (Template for credential structure)
│
└── config/                    ⚙️ Configuration files
    └── requirements.txt                (Python dependencies)
```

---

## 🚀 Quick Start

### For End Users (Recommended)

**Simply double-click:** `run_installer.bat`

That's it! The launcher will:
1. ✅ Check Python installation
2. ✅ Detect encrypted credentials in `keys/` folder
3. ✅ Install required packages if needed
4. ✅ Launch the GUI installer with automatic password loading

### Alternative: PowerShell Launcher

Right-click `run_installer.ps1` → "Run with PowerShell"

### Manual Launch

If you prefer to run manually:
```powershell
cd scripts
python debug_framework_installer.py
```

---

## 🔐 Encrypted Credentials

This package includes **encrypted credentials** for automatic installation:
- `keys/credentials.enc` - AES-256 encrypted credentials
- `keys/credentials.key` - Encryption key

**Security Notes:**
- ✅ Both files are required for installation
- ✅ Both files are excluded from Git (.gitignore)
- ✅ Safe to distribute together (encrypted)
- ⚠️ Keep these files secure - do not share publicly
- ⚠️ Only distribute through Intel-approved secure channels

**What's Encrypted:**
- FrameworkDefaultPass
- DANTA_DB_PASSWORD
- FrameworkDefaultUser
- SSH_PASSWORD (optional)

### No Credentials? No Problem!

If `keys/credentials.enc` is not present, the installer will:
1. Check environment variables
2. Prompt you to enter passwords interactively
3. Continue with installation

---

## 📋 Prerequisites

### Required
- **Python 3.8 or higher**
- **Windows 10/11** or Windows Server
- **PythonSV** (for framework usage after installation)

### Automatically Installed
The launcher will install these if missing:
- cryptography (for encrypted credentials)
- pandas, pymongo, xlwings, zeep (framework dependencies)
- Other packages from `config/requirements.txt`

---

## 🛠️ What Gets Installed

The installer will configure:

1. **Python Packages**
   - pandas, numpy (data processing)
   - pymongo (database)
   - xlwings, openpyxl (Excel)
   - cryptography (security)
   - zeep, colorama, tabulate, etc.

2. **Environment Variables**
   - FrameworkSerial (COM port)
   - FrameworkIPAdress (Linux IP)
   - FrameworkDefaultPass (from keys/credentials.enc)
   - FrameworkDefaultUser (from keys/credentials.enc)
   - DANTA_DB_PASSWORD (from keys/credentials.enc)

3. **TeraTerm Configuration**
   - COM port settings
   - Baud rate (115200)
   - Serial connection parameters

4. **Optional: EFI Content Transfer**
   - SSH/SCP transfer to Linux-booted units
   - Automatic startup file copying

---

## 📖 Documentation

### Quick References
- **This file** - Installation overview
- `docs/README_CREDENTIALS.md` - Credential management quick start
- `docs/CREDENTIALS_SETUP.md` - Complete credential setup guide

### Full Documentation
Located in parent directory:
- `../INSTALLATION_GUIDE.md` - Complete installation manual
- `../THR_DEBUG_FRAMEWORK_USER_MANUAL.md` - Framework user guide

---

## 🔧 Troubleshooting

### Issue: "Python not found"
**Solution:** Install Python 3.8+ from https://www.python.org/downloads/

### Issue: "cryptography not found"
**Solution:** Run `pip install --proxy http://proxy-dmz.intel.com:911 -r config\requirements.txt`

**Note:** Intel proxy is required for package installation. The launchers automatically use the proxy.

### Issue: "Failed to decrypt credentials"
**Cause:** Missing credentials.key or corrupted files

**Solution:**
1. Verify both `keys/credentials.enc` and `keys/credentials.key` exist
2. Contact package distributor for new files
3. Alternatively, remove both files and enter passwords manually

### Issue: "Installer won't start"
**Solution:**
1. Open Command Prompt as Administrator
2. Navigate to installation folder
3. Run: `python scripts\debug_framework_installer.py`
4. Check error messages

---

## 🔄 For Administrators: Recreating Credentials

If you need to create new encrypted credentials:

1. **Install cryptography**:
   ```powershell
   pip install --proxy http://proxy-dmz.intel.com:911 cryptography
   ```

2. **Edit** `scripts/create_credentials.py` with new passwords

3. **Run the creator**:
   ```powershell
   cd scripts
   python create_credentials.py
   ```

4. **Distribute new files**:
   - Files are automatically created in `keys/` folder
   - `keys/credentials.enc`
   - `keys/credentials.key`
   - Distribute through secure channels

**Detailed instructions:** See `docs/CREDENTIALS_SETUP.md`

---

## 📞 Support

**Primary Maintainer:**
- Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

**For Issues:**
- Open GitHub issue (do NOT include passwords)
- Contact your team lead
- Check internal documentation (Confluence, Wiki)

**Security Concerns:**
- Intel Security: security@intel.com
- Report credential leaks immediately

---

## 🎯 Next Steps After Installation

1. **Restart PythonSV** to load new environment variables
2. **Verify installation**:
   ```python
   import users.gaespino.DebugFramework.GNRSystemDebug as gdf
   gdf.Frameworkutils.platform_check(com_port=8, ip_address='192.168.0.2')
   ```
3. **Check documentation** in parent folder for framework usage
4. **Run your first test** - See examples in framework documentation

---

## 📜 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.7.1 | Feb 17, 2026 | Reorganized folder structure with subfolders |
|       |              | Added encrypted credentials system |
|       |              | Created unified launcher (run_installer.bat) |
|       |              | Added comprehensive documentation |

---

**Ready to install? Double-click `run_installer.bat` to begin!** 🚀
