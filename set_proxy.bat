@echo off
REM Set Intel Proxy Environment Variables
REM Usage: set_proxy.bat

echo Setting Intel proxy environment variables...

set http_proxy=http://proxy-dmz.intel.com:911
set https_proxy=http://proxy-dmz.intel.com:912
set no_proxy=localhost.intel.com,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16

echo.
echo [OK] http_proxy  = %http_proxy%
echo [OK] https_proxy = %https_proxy%
echo [OK] no_proxy    = %no_proxy%
echo.
echo Proxy configuration complete!
