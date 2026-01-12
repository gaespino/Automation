echo -off

if %1 eq "help" then
    goto help
endif

:varchecks
# =============================================================================
# VARIABLES CHECK
# =============================================================================

echo " "
echo " Setting Merlin variables for runregression script"
echo " "

if %1 eq "" then
    goto defaults
endif

if %2 eq "" then
    goto defaults
endif

if %3 eq "" then
    goto defaults
endif

:external
# =============================================================================
# EXTERNAL PARAMETERS
# =============================================================================

set MERLIN %1
set MERLIN_DRIVE %2
set MERLIN_DIR %3
set MERLIN_EXTRA " "

goto printvars

:defaults
# =============================================================================
# DEFAULT VALUES
# =============================================================================

# Default Values
set MERLIN_DIR fs1:\EFI\Version8.23\BinFiles\Release
set MERLIN_DRIVE fs1:
set MERLIN "MerlinX.efi"
set MERLIN_EXTRA " "

:printvars
echo MERLIN set to: %MERLIN%
echo MERLIN_DIR set to: %MERLIN_DIR%
echo MERLIN_DRIVE set to: %MERLIN_DRIVE%
echo MERLIN_EXTRA set to: %MERLIN_EXTRA%
goto end

:help
# =============================================================================
# Help
# =============================================================================
echo " "
echo USAGE:
echo   "MerlinSetup.nsh"
echo   "MerlinSetup.nsh ^<MERLIN^> ^<MERLIN_DRIVE^> ^<MERLIN_DIR^> "
echo " "
echo PARAMETERS:
echo " "
echo  " MERLIN_DRIVE           - Drive where MerlinX exists (default: fs1:)"
echo  " MERLIN_DIR             - Directory path to MerlinX (default: fs1:\EFI\Version8.15\BinFiles\Release)"
echo  " MERLIN                 - MerlinX executable name (default: MerlinX)"
echo  " MERLIN_EXTRA		   - MerlinX additional commands required for DMR (default: -otl -x2ar)"

:end