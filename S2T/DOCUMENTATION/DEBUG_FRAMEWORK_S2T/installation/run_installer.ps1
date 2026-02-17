#!/usr/bin/env pwsh
# ==============================================================================
# Debug Framework & S2T - Installation Launcher (PowerShell)
# ==============================================================================
# Version: 1.7.1
# Date: February 17, 2026
#
# This script launches the Debug Framework installer GUI.
#
# Prerequisites:
#   - Python 3.8 or higher
#   - credentials.enc and credentials.key files (for automatic password loading)
#
# Usage:
#   .\run_installer.ps1
#   or right-click and "Run with PowerShell"
# ==============================================================================

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================================================"
Write-Host "Debug Framework & S2T Installer v1.7.1"
Write-Host "========================================================================"
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if Python is installed
Write-Host "[INFO] Checking Python installation..."
try {
    $pythonVersion = & python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "[OK] $pythonVersion"
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.8 or higher from:"
    Write-Host "https://www.python.org/downloads/"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check for credentials files
$credFile = Join-Path $ScriptDir "keys\credentials.enc"
$keyFile = Join-Path $ScriptDir "keys\credentials.key"

if (Test-Path $credFile) {
    if (Test-Path $keyFile) {
        Write-Host "[OK] Encrypted credentials found - automatic password loading enabled" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] credentials.enc found but credentials.key is missing" -ForegroundColor Yellow
        Write-Host "         Installer will prompt for passwords"
    }
} else {
    Write-Host "[INFO] No encrypted credentials found"
    Write-Host "       Installer will prompt for passwords or use environment variables"
}

Write-Host ""

# Check if required packages are installed
Write-Host "[INFO] Checking for required packages..."
try {
    & python -c "import tkinter" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "tkinter not found"
    }
    Write-Host "[OK] tkinter found"
} catch {
    Write-Host "[ERROR] tkinter not found - required for GUI" -ForegroundColor Red
    Write-Host "        Please reinstall Python with tkinter support"
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    & python -c "from cryptography.fernet import Fernet" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] cryptography library not found" -ForegroundColor Yellow
        Write-Host "[INFO] Installing required packages..."
        $reqFile = Join-Path $ScriptDir "config\requirements.txt"
        & pip install --proxy http://proxy-dmz.intel.com:911 -r $reqFile
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install packages"
        }
        Write-Host "[OK] Packages installed successfully" -ForegroundColor Green
    } else {
        Write-Host "[OK] cryptography found"
    }
} catch {
    Write-Host "[ERROR] Failed to install required packages" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================================================"
Write-Host "Starting installer..."
Write-Host "========================================================================"
Write-Host ""

# Launch the installer
$installerPath = Join-Path $ScriptDir "scripts\debug_framework_installer.py"

try {
    & python $installerPath
    if ($LASTEXITCODE -ne 0) {
        throw "Installer exited with error code $LASTEXITCODE"
    }

    Write-Host ""
    Write-Host "========================================================================"
    Write-Host "Installation completed successfully"
    Write-Host "========================================================================"
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "[ERROR] Installer failed: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to exit"
