# Credentials Setup Guide

**Classification:** Intel Confidential - Do Not Share
**Purpose:** Secure credential management for Debug Framework
**Version:** 1.7.1
**Date:** February 17, 2026

---

## ⚠️ SECURITY NOTICE

**CRITICAL:** Passwords and credentials are **NOT stored in Git repositories** to comply with Intel security policies. This document explains how to securely obtain and configure required credentials.

---

## 🔐 RECOMMENDED: Encrypted Credentials System (NEW!)

**Version 1.7.1+ now supports encrypted credential storage!**

### Overview

Instead of manually entering passwords each time, you can:
1. Create an encrypted `credentials.enc` file containing all passwords
2. Distribute this file (and the encryption key) to end users in the `keys/` folder
3. The installer automatically decrypts and uses credentials

### Benefits

✅ **Secure Storage** - AES-256 encryption (Fernet)
✅ **Easy Distribution** - Single encrypted file for end users
✅ **No Git Commits** - Credentials stay out of version control
✅ **Password-Protected** - Optional password-based encryption
✅ **Automated Setup** - No manual password entry needed

### Quick Start

**For Administrators (Creating Credentials File):**

```powershell
# Navigate to installation folder
cd C:\Git\Automation\S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T\installation

# Create encrypted credentials
python credentials_manager.py create
```

Follow the prompts to:
1. Set an encryption password (optional but recommended)
2. Enter FrameworkDefaultPass
3. Enter DANTA_DB_PASSWORD
4. Optionally enter SSH password

This creates two files in the `keys/` folder:
- `keys/credentials.enc` - Encrypted credentials (share with end users)
- `keys/credentials.key` - Encryption key (share with end users)

**For End Users (Using Encrypted Credentials):**

The `keys/credentials.enc` and `keys/credentials.key` files should be placed in the `installation/keys/` folder. The installer will automatically detect and use them!

### Security Notes

⚠ **IMPORTANT:**
- Distribute `credentials.enc` and `credentials.key` through **secure channels only**
- Do NOT email these files in plaintext
- Do NOT commit these files to Git (already excluded via .gitignore)
- Use password-based encryption for extra security layer
- Rotate credentials periodically (re-create the .enc file)

### Alternative: Manual Entry

If you don't use encrypted credentials, the installer will prompt for passwords interactively (as before).

---

## Required Credentials

The Debug Framework requires the following credentials to function:

### 1. FrameworkDefaultPass
- **Purpose:** Default password for Linux-booted test units
- **Used by:** TeraTerm serial connections, SSH transfers, framework automation
- **Scope:** Test hardware units (non-production)

### 2. DANTA_DB_PASSWORD
- **Purpose:** Database authentication for DANTA tracking system
- **Used by:** S2T tools, test result logging, data queries
- **Scope:** Test database access

### 3. FrameworkDefaultUser
- **Purpose:** Default username for test units
- **Value:** `root` (non-sensitive, can be in documentation)
- **Used by:** SSH connections, serial console

---

## How to Obtain Credentials

**DO NOT EMAIL OR SHARE PASSWORDS IN PLAINTEXT**

### Option 1: Team Lead (Recommended)
Contact your team lead or manager:
- Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)
- Your direct supervisor
- Senior team members with framework access

Request credentials through **secure channels**:
- In-person communication
- Intel internal secure messaging
- Encrypted email (Intel-approved tools only)

### Option 2: Internal Documentation
Check Intel internal secure repositories:
- **Confluence:** Search for "Debug Framework Credentials" (restricted access)
- **SharePoint:** Team-specific secure document libraries
- **Wiki:** Internal test team wikis (password-protected pages)

### Option 3: Existing Environment
If you're setting up on a new machine but have access to an old one:
```powershell
# On your old machine, export environment variables
echo $env:FrameworkDefaultPass
echo $env:DANTA_DB_PASSWORD
```
**Note:** Write these down temporarily, then securely delete notes after setup.

---

## Setting Up Credentials

### Method 1: Encrypted Credentials File (RECOMMENDED - New in v1.7.1)

**Step 1: Install cryptography library**
```powershell
pip install --proxy http://proxy-dmz.intel.com:911 cryptography
```

**Step 2: Create encrypted credentials file**
```powershell
cd C:\Git\Automation\S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T\installation

# Run the credentials manager
python credentials_manager.py create
```

**Follow the prompts:**
```
Debug Framework - Encrypted Credentials Setup
==============================================================================

This utility creates an encrypted credentials file for the installer.
The encrypted file will be stored locally and NOT committed to Git.

⚠ SECURITY: Keep the credentials.enc and credentials.key files secure.
These files should be distributed to end users through secure channels.

Step 1: Set encryption password
----------------------------------------------------------------------
Use password-based encryption? (y/n, default=y): y
Enter encryption password: ********
Confirm password: ********

Step 2: Enter framework credentials
----------------------------------------------------------------------
Contact your team lead if you don't know these values.

FrameworkDefaultPass: ********
FrameworkDefaultUser (default=root): root
DANTA_DB_PASSWORD: ********

Optional: SSH Password for EFI transfer
SSH Password (press Enter to skip): ********

==============================================================================
✓ Credentials encrypted successfully!
==============================================================================

Files created:
  - credentials.enc (encrypted credentials)
  - credentials.key (encryption key)

⚠ IMPORTANT:
  1. Keep these files secure and do NOT commit to Git
  2. Distribute to end users through secure channels only
  3. .gitignore should exclude: credentials.enc, credentials.key
```

**Step 3: Distribute to end users**

Package the following files together:
- `credentials.enc`
- `credentials.key`
- `debug_framework_installer.py`
- `credentials_manager.py`
- `requirements.txt`
- Other installer files

**Step 4: End users run installer**

When end users run the installer with `credentials.enc` in the same folder, it will automatically load credentials - no manual entry needed!

---

### Method 2: Using the GUI Installer (Interactive)

1. Run the installer:
   ```powershell
   python installation/debug_framework_installer.py
   ```

2. During installation, if passwords are not found:
   - You'll be prompted with dialog boxes
   - Enter passwords when requested (they'll be hidden with `*`)
   - Or click "No" to skip and set manually later

3. Passwords are stored in Windows User environment variables (encrypted by Windows)

---

### Method 3: Using PowerShell Script

```powershell
cd C:\Git\Automation\S2T\DOCUMENTATION\DEBUG_FRAMEWORK_S2T\installation

# Run with password parameters
.\TeratermEnv.ps1 -com 8 -ip 192.168.0.2 `
    -frameworkPass "YOUR_PASSWORD_HERE" `
    -dantaDbPass "YOUR_DB_PASSWORD_HERE"

# Or run without passwords - you'll be prompted securely
.\TeratermEnv.ps1 -com 8 -ip 192.168.0.2
```

When prompted, enter passwords securely (they won't be displayed on screen).

---

### Method 4: Manual Environment Variable Setup

```powershell
# Set environment variables manually (User level)
setx FrameworkDefaultPass "YOUR_PASSWORD_HERE"
setx DANTA_DB_PASSWORD "YOUR_DB_PASSWORD_HERE"
setx FrameworkDefaultUser "root"
setx FrameworkSerial "8"
setx FrameworkIPAdress "192.168.0.2"
```

**Important:** Clear PowerShell history after setting passwords:
```powershell
Clear-History
Remove-Item (Get-PSReadlineOption).HistorySavePath
```

---

### Method 5: Windows Credential Manager (Advanced)

For maximum security, use Windows Credential Manager:

1. Open Windows Credential Manager
2. Add generic credentials:
   - Internet or network address: `DebugFramework`
   - User name: `FrameworkDefaultPass`
   - Password: `[your password]`

3. Modify framework code to read from Credential Manager instead of environment variables.

---

## Verifying Credentials

After setting credentials, verify they're available:

```powershell
# Check environment variables (PASSWORDS WILL BE DISPLAYED!)
echo $env:FrameworkDefaultPass
echo $env:DANTA_DB_PASSWORD

# Or check without displaying values
if ($env:FrameworkDefaultPass) { Write-Host "FrameworkDefaultPass: SET" } else { Write-Host "FrameworkDefaultPass: NOT SET" }
if ($env:DANTA_DB_PASSWORD) { Write-Host "DANTA_DB_PASSWORD: SET" } else { Write-Host "DANTA_DB_PASSWORD: NOT SET" }
```

**Reminder:** Restart PythonSV after setting environment variables.

---

## Security Best Practices

### ✅ DO:
- **USE encrypted credentials file (credentials.enc) for distribution** ⭐ NEW!
- Store passwords in Windows environment variables (User level)
- Use secure prompts (PowerShell `-AsSecureString` or tkinter password dialogs)
- Share credentials.enc through secure Intel-approved channels only
- Use password-based encryption for extra security layer
- Clear command history after manual password entry
- Rotate passwords periodically (recreate credentials.enc)
- Use Windows Credential Manager for enhanced security

### ❌ DON'T:
- **NEVER commit passwords, credentials.enc, or credentials.key to Git**
- Don't email credentials.enc without password protection
- Don't store passwords in text files or scripts
- Don't share passwords in Slack, Teams, or other chat platforms
- Don't write passwords on physical notes (or securely destroy after use)
- Don't use the same password for production systems
- Don't lose the credentials.key file (needed to decrypt credentials.enc)

---

## Troubleshooting

### Issue: "Failed to decrypt credentials file"

**Cause:** Wrong decryption password, corrupted file, or missing key file.

**Solution:**
1. Verify both `credentials.enc` and `credentials.key` exist in installation folder
2. If using password-based encryption, ensure correct password
3. Check file is not corrupted (try recreating with `python credentials_manager.py create`)
4. Verify cryptography library installed: `pip install --proxy http://proxy-dmz.intel.com:911 cryptography`

**Test decryption:**
```powershell
cd installation
python credentials_manager.py read
```

### Issue: "credentials_manager not available"

**Cause:** Missing credentials_manager.py or import error.

**Solution:**
1. Ensure `credentials_manager.py` is in the installation folder
2. Install cryptography: `pip install --proxy http://proxy-dmz.intel.com:911 cryptography`
3. Check for Python import errors: `python -c "from credentials_manager import CredentialsManager"`

### Issue: "No encrypted credentials file found"

**Explanation:** This is a warning, not an error. The installer will prompt for passwords interactively.

**Solution (if you want to use encrypted credentials):**
1. Create credentials file: `python credentials_manager.py create`
2. Place `credentials.enc` and `credentials.key` in installation folder
3. Re-run installer

### Issue: "FrameworkDefaultPass not found"

**Solution:**
1. Passwords were not set during installation
2. Run installer again or use Method 2/3 above
3. Restart PythonSV after setting

### Issue: "Access Denied" when running framework

**Solution:**
1. Wrong password - obtain correct password from team lead
2. Password not set - check with verification commands above
3. Environment variables not loaded - restart PythonSV

### Issue: "How do I rotate/change passwords?"

**Solution:**
1. Get new password from team lead
2. Run PowerShell script or use `setx` commands with new password
3. Notify team members if this is a team-wide change

### Issue: "I accidentally committed a password to Git"

**Solution:**
1. **IMMEDIATELY** notify your manager and security team
2. Rotate the password across all systems
3. Remove password from Git history:
   ```powershell
   git filter-branch --force --index-filter "git rm --cached --ignore-unmatch PATH_TO_FILE" --prune-empty --tag-name-filter cat -- --all
   ```
4. Force push to remote (coordinate with team)
5. Complete Intel security incident report

---

## Password Rotation Schedule

**Recommended:** Rotate passwords every 90 days or when:
- Team member leaves the team
- Suspected compromise
- After security incident
- Major project phase changes

**Coordination:** Password rotation must be coordinated across entire team to avoid service disruption.

---

## Support

**Security Concerns:**
- Intel Security: security@intel.com
- IT Security Helpdesk: (internal contact)

**Password Access Issues:**
- Gabriel Espinoza: gabriel.espinoza.ballestero@intel.com
- Your team lead or manager

**Technical Issues:**
- Open issue on GitHub (do NOT include passwords in issue descriptions)
- Contact framework maintainers

---

## Additional Notes

### Why Not in Git?

1. **Security Policy:** Intel policy prohibits credentials in source control
2. **Compliance:** SOX, PCI-DSS, and other regulations require secure credential management
3. **Risk Mitigation:** Git history is hard to clean completely
4. **Access Control:** Not all repository users need production access

### Alternative: HashiCorp Vault or Azure Key Vault

For enterprise deployments, consider:
- HashiCorp Vault for secret management
- Azure Key Vault integration
- CyberArk or similar password management systems

Contact IT Security for guidance on enterprise secret management.

---

**Document Classification:** Intel Confidential
**Last Updated:** February 17, 2026
**Maintainer:** Gabriel Espinoza
