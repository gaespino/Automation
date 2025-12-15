# Set Intel Proxy Environment Variables
# Usage: . .\set_proxy.ps1  (dot-source to set in current session)
#    or: .\set_proxy.ps1     (run in new scope)

Write-Host "Setting Intel proxy environment variables..." -ForegroundColor Cyan

$env:http_proxy = "http://proxy-dmz.intel.com:911"
$env:https_proxy = "http://proxy-dmz.intel.com:912"
$env:no_proxy = "localhost.intel.com,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

Write-Host "✓ http_proxy  = $env:http_proxy" -ForegroundColor Green
Write-Host "✓ https_proxy = $env:https_proxy" -ForegroundColor Green
Write-Host "✓ no_proxy    = $env:no_proxy" -ForegroundColor Green
Write-Host "`nProxy configuration complete!" -ForegroundColor Green
