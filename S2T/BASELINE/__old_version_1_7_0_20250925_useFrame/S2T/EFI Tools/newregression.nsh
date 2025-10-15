echo -off

# =============================================================================
# Dragon Regression Test Script v2.0
# Author: Brent Calhoon
# Support: Gabriel Espinoza
# =============================================================================

if %1 eq "help" then
    goto help
endif

if %1 eq "clear" then
    goto clear
endif

if %1 eq "next" then
    goto skipinit
endif

if %1 eq "" then
    echo ERROR: Need to pass in directory of OBJs
    goto help
endif

# =============================================================================
# INITIALIZATION
# =============================================================================

echo **************************************
echo *****  Dragon Regression v2.0    *****
echo **************************************

set OBJ_DIR %1
if not exist %OBJ_DIR% then 
    echo ERROR: OBJ_DIR %OBJ_DIR% does not exist
    goto help
endif

echo Running seeds in %OBJ_DIR%

# Set default variables if not already set
if "%MERLIN_DRIVE%" eq "" then
    set MERLIN_DRIVE "fs1:"
endif

if "%MERLIN_DIR%" eq "" then
    set MERLIN_DIR "fs1:\EFI\Version8.15\BinFiles\Release"
endif

if "%MERLIN%" eq "" then
    set MERLIN "MerlinX.efi"
endif

if "%MERLIN_EXTRA%" eq "" then
    set MERLIN_EXTRA " "
endif

if "%DRG_POST_EXE_CMD%" eq "" then
    set DRG_POST_EXE_CMD "echo"
endif

if "%DRG_RESUME_REGRESSION%" eq "" then
    set DRG_RESUME_REGRESSION 0
endif

if "%DRG_STOP_ON_FAIL%" eq "" then
    set DRG_STOP_ON_FAIL 0
endif

if "%DRG_RESET_ON_FAIL%" eq "" then
    set DRG_RESET_ON_FAIL 0
endif

if "%DRG_START_FRESH%" eq "" then
    set DRG_START_FRESH 1
endif

if "%DRG_CURRENT_SEED%" eq "" then
    set DRG_CURRENT_SEED "NONE"
endif

if "%VVAR2%" eq "" then
    set VVAR2 "0x1000000"
endif

if "%VVAR3%" eq "" then
    set VVAR3 "0x800000"
endif

#if "%VVAR4%" eq "" then
#    set VVAR4 " "
#endif

#if "%VVAR5%" eq "" then
#    set VVAR5 " "
#endif

if "%VVAR_EXTRA%" eq "" then
    set VVAR_EXTRA "0 0x04C4B40 1 80064000"
endif

if "%DRG_LOOP_FOREVER%" eq "" then
    set DRG_LOOP_FOREVER "0"
endif

:skipinit
# Build file pattern
set RE %OBJ_DIR%\*
if %2 neq "" then
    set RE %OBJ_DIR%"\*%2*"
endif

# =============================================================================
# SETUP MERLIN ENVIRONMENT
# =============================================================================

set MERLIN_COMMAND "%MERLIN% %MERLIN_EXTRA%"
echo MERLIN COMMAND: %MERLIN_COMMAND%

echo Switching to drive %MERLIN_DRIVE%
%MERLIN_DRIVE%
echo Changing to MerlinX directory: %MERLIN_DIR%
set ORIGINAL_CWD %cwd%
cd %MERLIN_DIR%

if not exist %MERLIN% then
    echo ERROR: MerlinX not found at %MERLIN_DIR%\%MERLIN%
    goto done
endif

# Clean up previous runs if requested
if %DRG_START_FRESH% eq 1 then 
    echo Cleaning previous run files...
    del -q %OBJ_DIR%\*.var
    del -q %OBJ_DIR%\*.run
    del -q %OBJ_DIR%\*.hng
    del -q %OBJ_DIR%\fail.txt
    del -q %OBJ_DIR%\log.txt
    set DRG_START_FRESH 0
endif

if "%VVAR4%" neq "" then
   if "%VVAR5%" eq "" then
      echo "!! Invalid configuration VVAR4 set but no VVAR5 found"
      goto done
   endif
      echo "!! Setting test with VVAR 4 and 5      
      set VVAR "2 %VVAR2% 3 %VVAR3% %VVAR_EXTRA% 4 %VVAR4% 5 %VVAR5%"
else
   set VVAR "2 %VVAR2% 3 %VVAR3% %VVAR_EXTRA%"
endif

# =============================================================================
# MAIN REGRESSION LOOP
# =============================================================================

echo Starting regression...
echo ************** >> %OBJ_DIR%\fail.txt

:main_loop

if not %2 == "" then
 echo " "
 echo !! Running seeds that includes: %2
 echo " "
 shift
else
 echo " "
 echo !! Running all seeds in Folder
 echo " "
endif

if %DRG_RESUME_REGRESSION% == 1 then
    echo Resuming regression...
endif

for %n in %RE%.obj
    # Handle resume logic
    if %DRG_CURRENT_SEED% neq "NONE" then
        if %n == %DRG_CURRENT_SEED% then
            if %DRG_RESUME_REGRESSION% == 1 then
                set DRG_RESUME_REGRESSION 0
                goto next_seed
            endif
        endif
    endif
    
    if %DRG_RESUME_REGRESSION% == 1 then
        echo Skipping %n (already run)
        goto next_seed
    endif
    
    # Skip if .skp file exists
    if exist %n.skp then
        goto next_seed
    endif
    
    # Verify seed file exists
    if not exist %n then 
        echo ERROR: %n not found
        goto done
    endif 
    
    # Run the test
    set DRG_CURRENT_SEED %n
    echo Running %n
    echo Running "%MERLIN_COMMAND% -a %n -d %VVAR%"
    echo Running "%MERLIN_COMMAND% -a %n -d %VVAR%" >> %OBJ_DIR%\log.txt
    echo Running %n >> %n.hng 
    %MERLIN_COMMAND% -a %n -d %VVAR%
    rm %n.hng
    
    # Check for failure
    if exist %n.var then
        echo FAILED: %n >> %OBJ_DIR%\fail.txt
        echo FAILED: %n
        
        if %DRG_RESET_ON_FAIL% == 1 then
            echo Resetting system due to failure...
            stall 3000000
            reset
        endif
        
        if %DRG_STOP_ON_FAIL% == 1 then
            echo Stopping regression due to failure
            goto test_failed
        endif
    else
        echo PASSED: %n >> %OBJ_DIR%\log.txt
        cat %OBJ_DIR%\fail.txt
    endif
    
    :next_seed
    %DRG_POST_EXE_CMD%
endfor

# Handle looping and multiple filters applies to first filter only
if %DRG_LOOP_FOREVER% == 1 then
    goto main_loop
endif

# Multiple Filters option
:filter_loop

if not %2 == "" then
    set RE %OBJ_DIR%"\*%2*"
    goto main_loop
endif

goto test_passed

# =============================================================================
# COMPLETION HANDLERS
# =============================================================================

:test_failed
echo    " "
echo    "======================================"
echo    "=        TEST STATUS: FAILED         ="
echo    "=         REGRESSION STOPPED         ="
echo    "======================================"
echo    "Test Failed"
goto cleanup

:test_passed
echo    " "
echo    "======================================="
echo    "=        TEST STATUS: PASSED          ="
echo    "=         REGRESSION FINISHED         ="
echo    "======================================="
echo    "Test Completed"
goto cleanup

:cleanup
echo REGRESSION INFO: %OBJ_DIR%\log.txt
echo FAILURE INFO: %OBJ_DIR%\fail.txt
echo CHANGING BACK TO DIR: %ORIGINAL_CWD%
cd %ORIGINAL_CWD%\
goto done

# =============================================================================
# HELP SECTION
# =============================================================================

:help
echo "######################################################################"
echo "########             Dragon Regression Test Script v2.0"
echo "######################################################################"
echo " "
echo USAGE:
echo   "runregression.nsh help"
echo   "runregression.nsh clear" 
echo   "runregression.nsh ^<OBJ_DIR^>"
echo   "runregression.nsh ^<OBJ_DIR^> ^<filter1^> [filter2] [...]"
echo   "runregression.nsh next ^<filter1^> [filter2] [...]"
echo " "
echo PARAMETERS:
echo   "OBJ_DIR    - Directory containing .obj seed files"
echo   "filter     - String to match in .obj filenames"
echo   "next       - Continues from a previous state, using previous variables and OBJ DIR"
echo   "clear      - Clears all runregression variables"
echo   "help       - Opens this help menu"
echo " "
echo ENVIRONMENT VARIABLES:
echo  " MERLIN_DRIVE           - Drive where MerlinX exists (default: fs1:)"
echo  " MERLIN_DIR             - Directory path to MerlinX (default: fs1:\EFI\Version8.15\BinFiles\Release)"
echo  " MERLIN                 - MerlinX executable name (default: MerlinX)"
echo  " MERLIN_EXTRA           - Additional MerlinX parameters"
echo  " DRG_START_FRESH        - Delete previous run files (default: 1)"
echo  " DRG_RESUME_REGRESSION  - Resume from DRG_CURRENT_SEED (default: 0)"
echo  " DRG_CURRENT_SEED       - Seed to resume from"
echo  " DRG_STOP_ON_FAIL       - Stop on first failure (default: 0)"
echo  " DRG_RESET_ON_FAIL      - Reset system on failure (default: 0)"
echo  " DRG_LOOP_FOREVER       - Run continuously only works with first filter (default: 0)"
echo  " DRG_POST_EXE_CMD       - Command to run after each test"
echo  " VVAR2                  - Dragon VVAR 2 input (default: 0x1000000)"
echo  " VVAR3                  - Dragon VVAR 3 input (default: 0x800000)"
echo  " VVAR_EXTRA             - Additional VVAR parameters"
echo  " "
echo EXAMPLES:
echo   "runregression.nsh seeds\"
echo   "runregression.nsh seeds\ test1 test2"
echo   "set DRG_STOP_ON_FAIL 1 ^& runregression.nsh seeds\"
echo  " "
goto done

:clear
# =============================================================================
# VARIABLE CLEAR SECTION
# =============================================================================

# Clears All Variables if there is any set

echo "!! Clearing all Runregression variables"

if "%MERLIN_DRIVE%" neq "" then 
    echo "MERLIN_DRIVE removed"
    set MERLIN_DRIVE ""
else
    echo "MERLIN_DRIVE not set"
endif

if "%MERLIN_DIR%" neq "" then 
    echo "MERLIN_DIR removed"
    set MERLIN_DIR ""
else
    echo "MERLIN_DIR not set"
endif

if "%MERLIN%" neq "" then 
    echo "MERLIN removed"
    set MERLIN ""
else
    echo "MERLIN not set"
endif

if "%MERLIN_EXTRA%" neq "" then 
    echo "MERLIN_EXTRA removed"
    set MERLIN_EXTRA ""
else
    echo "MERLIN_EXTRA not set"
endif

if "%DRG_POST_EXE_CMD%" neq "" then 
    echo "DRG_POST_EXE_CMD removed"
    set DRG_POST_EXE_CMD ""
else
    echo "DRG_POST_EXE_CMD not set"
endif

if "%DRG_RESUME_REGRESSION%" neq "" then 
    echo "DRG_RESUME_REGRESSION removed"
    set DRG_RESUME_REGRESSION ""
else
    echo "DRG_RESUME_REGRESSION not set"
endif

if "%DRG_STOP_ON_FAIL%" neq "" then 
    echo "DRG_STOP_ON_FAIL removed"
    set DRG_STOP_ON_FAIL ""
else
    echo "DRG_STOP_ON_FAIL not set"
endif

if "%DRG_RESET_ON_FAIL%" neq "" then 
    echo "DRG_RESET_ON_FAIL removed"
    set DRG_RESET_ON_FAIL ""
else
    echo "DRG_RESET_ON_FAIL not set"
endif

if "%DRG_START_FRESH%" neq "" then 
    echo "DRG_START_FRESH removed"
    set DRG_START_FRESH ""
else
    echo "DRG_START_FRESH not set"
endif

if "%DRG_CURRENT_SEED%" neq "" then 
    echo "DRG_CURRENT_SEED removed"
    set DRG_CURRENT_SEED ""
else
    echo "DRG_CURRENT_SEED not set"
endif

if "%VVAR2%" neq "" then 
    echo "VVAR2 removed"
    set VVAR2 ""
else
    echo "VVAR2 not set"
endif

if "%VVAR3%" neq "" then 
    echo "VVAR3 removed"
    set VVAR3 ""
else
    echo "VVAR3 not set"
endif

if "%VVAR4%" neq "" then 
    echo "VVAR4 removed"
    set VVAR4 ""
else
    echo "VVAR4 not set"
endif

if "%VVAR5%" neq "" then 
    echo "VVAR5 removed"
    set VVAR5 ""
else
    echo "VVAR5 not set"
endif

if "%VVAR_EXTRA%" neq "" then 
    echo "VVAR_EXTRA removed"
    set VVAR_EXTRA ""
else
    echo "VVAR_EXTRA not set"
endif

if "%DRG_LOOP_FOREVER%" neq "" then 
    echo "DRG_LOOP_FOREVER removed"
    set DRG_LOOP_FOREVER ""
else
    echo "DRG_LOOP_FOREVER not set"
endif

:done