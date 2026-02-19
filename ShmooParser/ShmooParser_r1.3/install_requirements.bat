@echo off
REM ============================================================================
REM ShmooParser - Install Requirements with Intel Proxy
REM ============================================================================
REM This script installs all required Python packages using Intel's proxy
REM ============================================================================

echo.
echo ========================================================================
echo Installing ShmooParser Requirements
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python found:
python --version
echo.

REM Install requirements using Intel proxy
echo [INFO] Installing packages with Intel proxy...
echo.

pip install -r requirements.txt --proxy=http://proxy-chain.intel.com:911

if errorlevel 1 (
    echo.
    echo [WARNING] Installation with proxy-chain failed, trying alternative proxy...
    echo.
    pip install -r requirements.txt --proxy=http://proxy-dmz.intel.com:911

    if errorlevel 1 (
        echo.
        echo [ERROR] Installation failed with both proxies
        echo Please check your network connection and proxy settings
        pause
        exit /b 1
    )
)

echo.
echo ========================================================================
echo Installation completed successfully!
echo ========================================================================
echo.
pause
