@echo off
REM Universal Deployment Tool Launcher
REM Deploys BASELINE/BASELINE_DMR/PPV to product-specific locations

cd /d "%~dp0"
python deploy_universal.py
pause
