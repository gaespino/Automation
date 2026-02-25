@echo off
REM ============================================================================
REM PPV Tools - Installation Script for Windows
REM ============================================================================
REM This script installs all required Python packages for PPV Tools
REM Run this script from the PPV folder
REM ============================================================================

echo.
echo ============================================================================
echo   PPV TOOLS - DEPENDENCY INSTALLER
echo ============================================================================
echo.
echo This script will install all required Python packages for PPV Tools.
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from python.org
    pause
    exit /b 1
)

echo Python detected:
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not installed or not in PATH
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo pip detected:
pip --version
echo.

echo ============================================================================
echo   INSTALLING DEPENDENCIES
echo ============================================================================
echo.

REM Upgrade pip first
echo [1/6] Upgrading pip to latest version...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing with current version...
)
echo.

REM Install pandas
echo [2/6] Installing pandas (Data Processing)...
pip install "pandas>=1.3.0"
if errorlevel 1 (
    echo ERROR: Failed to install pandas
    pause
    exit /b 1
)
echo.

REM Install numpy
echo [3/6] Installing numpy (Numerical Computing)...
pip install "numpy>=1.20.0"
if errorlevel 1 (
    echo ERROR: Failed to install numpy
    pause
    exit /b 1
)
echo.

REM Install openpyxl
echo [4/6] Installing openpyxl (Excel File Handling)...
pip install "openpyxl>=3.0.0"
if errorlevel 1 (
    echo ERROR: Failed to install openpyxl
    pause
    exit /b 1
)
echo.

REM Install xlwings
echo [5/6] Installing xlwings (Excel Automation)...
pip install "xlwings>=0.24.0"
if errorlevel 1 (
    echo ERROR: Failed to install xlwings
    pause
    exit /b 1
)
echo.

REM Install colorama and tabulate
echo [6/6] Installing colorama and tabulate (Console Formatting)...
pip install "colorama>=0.4.4" "tabulate>=0.8.9"
if errorlevel 1 (
    echo ERROR: Failed to install colorama/tabulate
    pause
    exit /b 1
)
echo.

echo ============================================================================
echo   VERIFYING INSTALLATION
echo ============================================================================
echo.

REM Verify installations
echo Verifying installed packages...
python -c "import pandas; print('✓ pandas', pandas.__version__)"
python -c "import numpy; print('✓ numpy', numpy.__version__)"
python -c "import openpyxl; print('✓ openpyxl', openpyxl.__version__)"
python -c "import xlwings; print('✓ xlwings', xlwings.__version__)"
python -c "import colorama; print('✓ colorama', colorama.__version__)"
python -c "import tabulate; print('✓ tabulate', tabulate.__version__)"
python -c "import tkinter; print('✓ tkinter (GUI framework)')"
echo.

echo ============================================================================
echo   INSTALLATION COMPLETE!
echo ============================================================================
echo.
echo All required packages have been successfully installed.
echo.
echo You can now run PPV Tools:
echo   - PPV Tools Hub:         python run.py
echo   - Experiment Builder:    python run_experiment_builder.py
echo   - Run Tests:            python test_experiment_builder.py
echo.
echo For more information, see README.md
echo.
pause
