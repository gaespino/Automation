# Launch Markdown Converter GUI
# PowerShell launcher script

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Launching Markdown Converter GUI..." -ForegroundColor Cyan

try {
    python md_converter_gui.py
}
catch {
    Write-Host "`nERROR: Failed to launch GUI" -ForegroundColor Red
    Write-Host "Make sure Python is installed and in your PATH" -ForegroundColor Yellow
    Read-Host "`nPress Enter to exit"
}
