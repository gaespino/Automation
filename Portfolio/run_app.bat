@echo off
SETLOCAL EnableDelayedExpansion
TITLE Portfolio App Launcher
cd /d "%~dp0"

echo ===================================================
echo     Portfolio - THR Tools + Dashboard Launcher
echo ===================================================
echo.

:: Ask for port (default 8000)
SET /P APP_PORT="Enter port to use [default: 8000]: "
IF "!APP_PORT!"=="" SET APP_PORT=8000

:: Validate port is numeric
echo !APP_PORT!| findstr /r "^[0-9][0-9]*$" >nul 2>&1
IF !ERRORLEVEL! NEQ 0 (
    echo [WARNING] Invalid port "!APP_PORT!", using 8000.
    SET APP_PORT=8000
)

echo.
echo   Dashboard:   http://localhost:!APP_PORT!/dashboard/
echo   THR Tools:   http://localhost:!APP_PORT!/thr/
echo   API Docs:    http://localhost:!APP_PORT!/docs
echo   Health:      http://localhost:!APP_PORT!/health
echo ===================================================
echo.

:: Check for any process already listening on that port
FOR /F "tokens=5" %%P IN ('netstat -ano 2^>nul ^| findstr /r "[:.]!APP_PORT! " ^| findstr "LISTENING"') DO (
    SET EXISTING_PID=%%P
)
IF DEFINED EXISTING_PID (
    echo [WARNING] Port !APP_PORT! is already in use by PID !EXISTING_PID!.
    FOR /F "tokens=1 skip=3" %%N IN ('tasklist /FI "PID eq !EXISTING_PID!" 2^>nul') DO SET EXISTING_NAME=%%N
    IF DEFINED EXISTING_NAME echo          Process: !EXISTING_NAME!
    echo.
    SET /P KILL_IT="Kill it and continue? [Y/N, default: Y]: "
    IF /I "!KILL_IT!"=="" SET KILL_IT=Y
    IF /I "!KILL_IT!"=="Y" (
        echo [INFO] Killing PID !EXISTING_PID!...
        taskkill /PID !EXISTING_PID! /F >nul 2>&1
        timeout /t 1 >nul
        echo [INFO] Process killed.
    ) ELSE (
        echo [ABORT] Cannot start while port !APP_PORT! is in use.
        pause
        exit /b 1
    )
)
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
echo [INFO] Starting Portfolio server on http://localhost:!APP_PORT! ...
echo [INFO]   Dashboard : http://localhost:!APP_PORT!/dashboard/
echo [INFO]   THR Tools : http://localhost:!APP_PORT!/thr/
echo [INFO]   API Docs  : http://localhost:!APP_PORT!/docs
echo.

start /b "" cmd /c "timeout /t 2 >nul && start http://localhost:!APP_PORT!/thr/"

uvicorn api.main:app --host 0.0.0.0 --port !APP_PORT!

pause
