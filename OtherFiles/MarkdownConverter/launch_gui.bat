@echo off
REM Launch Markdown Converter GUI

title Markdown Converter GUI

cd /d "%~dp0"

python md_converter_gui.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to launch GUI
    echo.
    echo Make sure Python is installed and in your PATH
    echo.
    pause
)
