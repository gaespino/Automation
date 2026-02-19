# ============================================================================
# ShmooParser - Install Requirements with Intel Proxy (PowerShell)
# ============================================================================
# This script installs all required Python packages using Intel's proxy
# ============================================================================

Write-Host ""
Write-Host "========================================================================"
Write-Host "Installing ShmooParser Requirements"
Write-Host "========================================================================"
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Python found:"
    Write-Host $pythonVersion
    Write-Host ""
}
catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from: https://www.python.org/downloads/"
    Read-Host "Press Enter to exit"
    exit 1
}

# Install requirements using Intel proxy
Write-Host "[INFO] Installing packages with Intel proxy..."
Write-Host ""

$result = pip install -r requirements.txt --proxy=http://proxy-chain.intel.com:911 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[WARNING] Installation with proxy-chain failed, trying alternative proxy..." -ForegroundColor Yellow
    Write-Host ""

    $result = pip install -r requirements.txt --proxy=http://proxy-dmz.intel.com:911 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERROR] Installation failed with both proxies" -ForegroundColor Red
        Write-Host "Please check your network connection and proxy settings"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "========================================================================"
Write-Host "Installation completed successfully!"
Write-Host "========================================================================"
Write-Host ""
Read-Host "Press Enter to exit"
