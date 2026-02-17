@echo off
REM ==============================================================================
REM Debug Framework & S2T - Installation Launcher
REM ==============================================================================
REM Version: 1.7.1
REM Date: February 17, 2026
REM
REM This script launches the Debug Framework installer GUI.
REM
REM Prerequisites:
REM   - Python 3.8 or higher
REM   - credentials.enc and credentials.key files (for automatic password loading)
REM
REM Usage:
REM   Simply double-click this file or run from command prompt
REM ==============================================================================

echo.
echo ========================================================================
echo Debug Framework ^& S2T Installer v1.7.1
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version
echo.

REM Check for credentials files
if exist "keys\credentials.enc" (
    if exist "keys\credentials.key" (
        echo [OK] Encrypted credentials found - automatic password loading enabled
    ) else (
        echo [WARNING] keys\credentials.enc found but keys\credentials.key is missing
        echo Installer will prompt for passwords
    )
) else (
    echo [INFO] No encrypted credentials found
    echo Installer will prompt for passwords or use environment variables
)
echo.

REM Check if required packages are installed
echo [INFO] Checking for required packages...
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] tkinter not found - required for GUI
    echo Please reinstall Python with tkinter support
    pause
    exit /b 1
)

python -c "from cryptography.fernet import Fernet" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] cryptography library not found
    echo Installing required packages...
    pip install --proxy http://proxy-dmz.intel.com:911 -r config\requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install packages
        pause
        exit /b 1
    )
) else (
    echo [OK] Required packages found
)

echo.
echo ========================================================================
echo Starting installer...
echo ========================================================================
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Launch the installer from scripts subfolder
python "%SCRIPT_DIR%scripts\debug_framework_installer.py"

if errorlevel 1 (
    echo.
    echo [ERROR] Installer exited with error
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo Installation completed
echo ========================================================================
echo.
pause
