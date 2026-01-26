@echo off
REM Add Python and pip to PATH
REM Usage: set_python_path.bat

echo Adding Python to PATH...

set PYTHON_HOME=C:\Users\gaespino\AppData\Local\Programs\Python\Python314

REM Add Python and Scripts to PATH
set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%

echo.
echo [OK] PYTHON_HOME = %PYTHON_HOME%
echo [OK] PATH includes Python and pip
echo.
echo Testing Python...
python --version

echo.
echo Testing pip...
pip --version

echo.
echo Python PATH configuration complete!
