# Debug Framework Release Notes Generator
# Quick launcher script for generating release documentation
# Usage: .\launch_release_notes.ps1

param(
    [string]$StartDate,
    [string]$Version,
    [switch]$SkipHTML
)

Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Debug Framework Release Notes Generator v1.0          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Change to DEVTOOLS directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$devtoolsPath = Split-Path -Parent $scriptPath
Set-Location $devtoolsPath

# Get parameters if not provided
if (-not $StartDate) {
    Write-Host "📅 Last release date (YYYY-MM-DD format)" -ForegroundColor Yellow
    Write-Host "   Example: 2026-01-22" -ForegroundColor Gray
    $StartDate = Read-Host "   Enter date"

    if ($StartDate -notmatch '^\d{4}-\d{2}-\d{2}$') {
        Write-Host "❌ Invalid date format. Use YYYY-MM-DD" -ForegroundColor Red
        exit 1
    }
}

if (-not $Version) {
    Write-Host ""
    Write-Host "📦 New version number" -ForegroundColor Yellow
    Write-Host "   Example: 1.8.0" -ForegroundColor Gray
    $Version = Read-Host "   Enter version"

    if ($Version -notmatch '^\d+\.\d+(\.\d+)?$') {
        Write-Host "❌ Invalid version format. Use X.Y or X.Y.Z" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Start Date: $StartDate" -ForegroundColor White
Write-Host "  Version:    $Version" -ForegroundColor White
Write-Host "  HTML:       $(-not $SkipHTML)" -ForegroundColor White
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Confirm before proceeding
$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Host "❌ Cancelled by user" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🚀 Generating release notes..." -ForegroundColor Green
Write-Host ""

# Build command
$command = "python generate_release_notes.py --start-date $StartDate --version $Version"
if (-not $SkipHTML) {
    $command += " --html"
}

# Run the generator
Write-Host "⚙️  Running: $command" -ForegroundColor Gray
Invoke-Expression $command

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Error generating release notes" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Release notes generated successfully!" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Display next steps
Write-Host "📋 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Review the generated draft:" -ForegroundColor White
Write-Host "   deploys\DRAFT_RELEASE_v${Version}_*.md" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Create full release document:" -ForegroundColor White
Write-Host "   • Add detailed feature descriptions" -ForegroundColor Gray
Write-Host "   • Organize by product [Common], [GNR/CWF], [DMR]" -ForegroundColor Gray
Write-Host "   • Include known issues and workarounds" -ForegroundColor Gray
Write-Host "   • Add upgrade instructions" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Create release email:" -ForegroundColor White
Write-Host "   • Start with HIGHLIGHTS section (10-12 bullets)" -ForegroundColor Gray
Write-Host "   • Add upgrade instructions (3 steps)" -ForegroundColor Gray
Write-Host "   • Include detailed features and fixes" -ForegroundColor Gray
Write-Host "   • Mark NEW features with ⭐ NEW" -ForegroundColor Gray
Write-Host ""

if (-not $SkipHTML) {
    Write-Host "4. Review HTML output:" -ForegroundColor White
    Write-Host "   deploys\release_files\*.html" -ForegroundColor Gray
    Write-Host ""

    # Ask if user wants to open HTML
    $openHTML = Read-Host "Open HTML file? (Y/N)"
    if ($openHTML -eq 'Y' -or $openHTML -eq 'y') {
        $htmlFiles = Get-ChildItem "deploys\release_files\*.html" -ErrorAction SilentlyContinue |
                     Sort-Object LastWriteTime -Descending |
                     Select-Object -First 1

        if ($htmlFiles) {
            Start-Process $htmlFiles.FullName
            Write-Host "✅ Opened HTML file in browser" -ForegroundColor Green
        } else {
            Write-Host "⚠️  No HTML files found" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "📚 Reference Files:" -ForegroundColor Yellow
Write-Host "   • QUICKSTART_RELEASE.md - Quick reference guide" -ForegroundColor Gray
Write-Host "   • RELEASE_TEMPLATE.md - Complete process guide" -ForegroundColor Gray
Write-Host "   • RELEASE_v1.7.1_Feb2026.md - Example release doc" -ForegroundColor Gray
Write-Host "   • RELEASE_EMAIL_v1.7.1_Feb2026.md - Example email" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 For AI/Copilot: See QUICKSTART_RELEASE.md" -ForegroundColor Magenta
Write-Host ""
