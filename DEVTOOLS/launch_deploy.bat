@echo off
REM PPV Deployment Tool Launcher
REM Quick launcher for the deployment GUI

echo ========================================
echo   PPV Deployment Tool
echo ========================================
echo.
echo Starting deployment tool...
echo.

python deploy_ppv.py

if errorlevel 1 (
    echo.
    echo Error: Deployment tool failed to start
    echo Please check that Python is installed and in your PATH
    pause
)
