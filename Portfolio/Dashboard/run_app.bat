@echo off
SETLOCAL EnableDelayedExpansion
TITLE Bucket Dashboard Launcher
cd /d "%~dp0"

echo ===================================================
echo      Bucket Dashboard (Light Version) Launcher
echo ===================================================
echo.

:: 1. Check Python Availability
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in your PATH!
    echo.
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo IMPTORANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Display Python Version
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo [CHECK] Found %PYTHON_VER%

:: 2. Virtual Environment Check & Creation
IF NOT EXIST "venv" (
    echo [INFO] Virtual environment not found. Creating 'venv'...
    python -m venv venv
    IF !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created.
) ELSE (
    echo [CHECK] Virtual environment found.
)

:: 3. Activate VENV
call venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)
echo [INFO] Virtual environment activated.

:: 4. Install Dependencies
IF EXIST "requirements.txt" (
    echo [INFO] Checking/Installing dependencies...
    pip install --upgrade --pre -r requirements.txt
    IF !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
) ELSE (
    echo [WARNING] requirements.txt not found. Skipping dependency installation.
)

:: 5. Launch Application
echo.
echo [INFO] Starting Bucket Dashboard...
echo [INFO] Browser will open automatically once the server starts...

:: Run App
python app.py

pause
