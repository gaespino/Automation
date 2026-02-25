@echo off
cd /d "%~dp0"
echo ============================================
echo  TP Migration Tool
echo ============================================
echo.

:: Check if flask is installed, install if not
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing requirements...
    pip install -r requirements.txt
    echo.
)

echo Starting TP Migration Tool at http://localhost:5050
echo Press Ctrl+C to stop.
echo.
python tp_migration.py
pause
