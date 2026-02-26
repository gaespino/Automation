@echo off
echo Starting THRHUB...

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+ and try again.
    pause
    exit /b 1
)

:: Check for Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Install Node.js 18+ and try again.
    pause
    exit /b 1
)

:: Install Python deps
echo Installing Python dependencies...
pip install -r backend\requirements.txt --quiet

:: Build React frontend
echo Building React frontend...
cd frontend
call npm install --silent
call npm run build
cd ..

:: Launch backend (serves both API + React SPA)
echo.
echo THRHUB is starting on http://localhost:5050
echo Press Ctrl+C to stop.
echo.
cd backend
python app.py
