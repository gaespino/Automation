@echo off
SETLOCAL EnableDelayedExpansion
TITLE Portfolio App Launcher
cd /d "%~dp0"

echo ===================================================
echo     Portfolio - THR Tools + Dashboard Launcher
echo ===================================================
echo.
echo   Dashboard:   http://localhost:8000/dashboard/
echo   THR Tools:   http://localhost:8000/thr/
echo   API Docs:    http://localhost:8000/docs
echo   Health:      http://localhost:8000/health
echo ===================================================
echo.

:: 1. Check Python Availability
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not found in your PATH!
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
echo [CHECK] Found %PYTHON_VER%

:: 2. Virtual Environment
IF NOT EXIST "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    IF !ERRORLEVEL! NEQ 0 ( echo [ERROR] Failed to create venv. & pause & exit /b 1 )
    echo [SUCCESS] Virtual environment created.
) ELSE (
    echo [CHECK] Virtual environment found.
)

:: 3. Activate VENV
call venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 ( echo [ERROR] Failed to activate venv. & pause & exit /b 1 )
echo [INFO] Virtual environment activated.

:: 4. Install Python Dependencies
IF EXIST "requirements.txt" (
    echo [INFO] Installing Python dependencies...
    pip install --upgrade -r requirements.txt
    IF !ERRORLEVEL! NEQ 0 ( echo [ERROR] Dependency install failed. & pause & exit /b 1 )
) ELSE (
    echo [WARNING] requirements.txt not found.
)

:: 5. Build React UI (once only - skip if dist already present)
IF EXIST "thr_ui\dist\index.html" (
    echo [CHECK] React build found at thr_ui\dist\
) ELSE (
    echo [INFO] React build not found. Checking for Node.js...
    node --version >nul 2>&1
    IF !ERRORLEVEL! EQU 0 (
        echo [INFO] Building React UI...
        cd thr_ui
        call npm install
        call npm run build
        cd ..
    ) ELSE (
        echo [WARNING] Node.js not found. THR Tools UI at /thr/ unavailable until built.
        echo           Install Node.js from https://nodejs.org/ then run:
        echo             cd thr_ui ^&^& npm install ^&^& npm run build
    )
)

:: 6. Launch FastAPI + uvicorn
echo.
echo [INFO] Starting Portfolio server on http://localhost:8000 ...
echo [INFO]   Dashboard : http://localhost:8000/dashboard/
echo [INFO]   THR Tools : http://localhost:8000/thr/
echo [INFO]   API Docs  : http://localhost:8000/docs
echo.

start /b "" cmd /c "timeout /t 2 >nul && start http://localhost:8000/thr/"

uvicorn api.main:app --host 0.0.0.0 --port 8000

pause
