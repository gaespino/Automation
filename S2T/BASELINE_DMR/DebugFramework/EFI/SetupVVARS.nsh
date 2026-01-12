echo -off

if %1 eq "help" then
    goto help
endif

:varchecks
# =============================================================================
# VARIABLES CHECK
# =============================================================================

echo " "
echo " Setting VVARs for runregression script"
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

if %4 eq "" then
    goto defaults   
endif


:external
# =============================================================================
# EXTERNAL PARAMETERS
# =============================================================================

# Set Variables if configured except EXTRA
set VVAR0 %1
set VVAR1 %2
set VVAR2 %3
set VVAR3 %4

if %5 eq "" then
    set VVAR_EXTRA " "
else
    set VVAR_EXTRA %5
endif

goto printvars

:defaults
# =============================================================================
# DEFAULT VALUES
# =============================================================================

set VVAR0 "0x4C4B40"
set VVAR1 "80064000"
set VVAR2 "0x1000000"
set VVAR3 "0x4210000"
set VVAR_EXTRA " "

:printvars
echo VVAR0 set to: %VVAR0%
echo VVAR1 set to: %VVAR1%
echo VVAR2 set to: %VVAR2%
echo VVAR3 set to: %VVAR3%
echo VVAR_EXTRA set to: %VVAR_EXTRA%
goto end


:help
# =============================================================================
# Help
# =============================================================================
echo " "
echo USAGE:
echo   "VVARSetup.nsh"
echo   "VVARSetup.nsh ^<VVAR0^> ^<VVAR1^> ^<VVAR2^> ^<VVAR3^> ^<VVAR_EXTRA^> "
echo " "
echo PARAMETERS:
echo  " VVAR0                  - Dragon VVAR 0: Test Runtime (default: 0x04C4B40)"
echo  " VVAR1                  - Dragon VVAR 1: Exec. Time in CPU Cycles (default: 80064000)"
echo  " VVAR2                  - Dragon VVAR 2: Thread Count (default: 0x1000000)"
echo  " VVAR3                  - Dragon VVAR 3: Debug Flags (default: 0x800000)"
echo  " VVAR_EXTRA             - Additional VVAR parameters"

:end