# Add Python and pip to PATH
# Usage: .\set_python_path.ps1

Write-Host "Searching for Python installation..." -ForegroundColor Cyan

# Get current user
$currentUser = $env:USERNAME

# Common Python installation locations
$searchPaths = @(
    "C:\Users\$currentUser\AppData\Local\Programs\Python",
    "C:\Program Files\Python",
    "C:\Python"
)

$pythonHome = $null

# Search for Python installation
foreach ($searchPath in $searchPaths) {
    if (Test-Path $searchPath) {
        # Find Python3xx folders
        $pythonFolders = Get-ChildItem -Path $searchPath -Directory -Filter "Python3*" -ErrorAction SilentlyContinue |
                         Sort-Object Name -Descending

        if ($pythonFolders) {
            $pythonHome = $pythonFolders[0].FullName
            break
        }
    }
}

if (-not $pythonHome) {
    Write-Host "[ERROR] Python installation not found!" -ForegroundColor Red
    Write-Host "Searched in: $($searchPaths -join ', ')" -ForegroundColor Yellow
    exit 1
}

# Add Python and Scripts to PATH for current session
$env:PATH = "$pythonHome;$pythonHome\Scripts;$env:PATH"

Write-Host ""
Write-Host "[OK] Found Python at: $pythonHome" -ForegroundColor Green
Write-Host "[OK] Added to PATH for current session" -ForegroundColor Green
Write-Host ""

# Test Python
Write-Host "Testing Python..." -ForegroundColor Cyan
& python --version

Write-Host ""

# Test pip
Write-Host "Testing pip..." -ForegroundColor Cyan
& pip --version

Write-Host ""
Write-Host "Python PATH configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Note: This change is only for the current session." -ForegroundColor Yellow
Write-Host "To make it permanent, add Python to your System PATH in Environment Variables." -ForegroundColor Yellow
