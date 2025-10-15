echo -off

if %1 eq "help" then
:help
echo run this script from the directory that contains the seeds.
echo Usage:
echo     runregression.nsh <OBJ DIR> : runs all OBJs in the directory
echo     runregression.nsh <OBJ DIR> <match string>: Runs all OBJS that contain the <string>
echo Overrides are done via EFI VARIABLES: (you will likely need to set up MERLIN VARIABLES!!!!) 
echo setup variables via "set <sname> <value>"
echo DRG_RESUME_REGRESSION: if set == 1, resume regression starting with seed after %CURRENT_SEED% 
echo MERLIN_DIR: Directory where MerlinX exists  (default = fs0:\) 
echo MERLIN_DRIVE: Drive where MERLIN_DIR exists (default = fs0:)
echo MERLIN: Name of MerlinX : (default = merlinx) 
echo DRG_START_FRESH : If set, delete log files and var files.
echo DRG_CLEAN_ALL : If set, resets all variables
echo DRG_CURRENT_SEED: Current seed being run. Used for resuming regression
echo VVAR2 : Dragon VVAR 2 input. 1 value
echo VVAR3 : Dragon VVAR 3 input. 1 value
echo VVAR4 : Dragon VVAR 4 input. 1 value
echo VVAR5 : Dragon VVAR 5 input. 1 value
echo VVAR_EXTRA : Additional vvar parameters. Must be <VVAR> <VVAR_VAL>. Use quotes around VVAR VVAR_VAL when setting it
echo MERLIN_EXTRA : Additional merlin parameters.
echo DRG_LOOP_FOREVER: if set==1, keep running forever 
echo "%1 input %" --> does a regular expression on all OBJs
echo DRG_STOP_ON_FAIL--> if set==1, exit on first fail ( when <obj>.var is present)
echo DRG_RESET_ON_FAIL--> if set==1, resets system on first fail ( when <obj>.var is present)
echo DRG_POST_EXE_CMD --> will execute this command on every loop
goto done
endif 

# If anyone knows a different way to determine if a variable exists,please fix this script!
echo **************************************
echo ***** runregression version 1.12 *****
echo ***** contact: Brent Calhoon     *****
echo **************************************

if %1 eq "" then
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo !!!!!! Need to pass in directory of OBJs !!!!!
    echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    echo 
    echo 
    echo 
    echo 
    goto help
endif
set OBJ_DIR %1
if exist %OBJ_DIR% then 
   echo running seeds in %OBJ_DIR%
else
   echo !!!!! OBJ_DIR is not set!!!! 
   goto help
endif

set RE %OBJ_DIR%\*
if %2 neq "" then
   set RE %OBJ_DIR%"\*%2*"
endif

if exist TEMP.txt then
    del -q TEMP.txt
endif

echo TEMP >> %MERLIN_DRIVE_SET%TEMP.txt
if not exist TEMP.txt then
    del -q %MERLIN_DRIVE_SET%TEMP.txt
endif
if exist TEMP.txt then
    set MERLIN_DRIVE "fs0:" 
    set MERLIN_DRIVE_SET TRUE
    del -q TEMP.txt
endif

echo TEMP >> %MERLIN_DIR_SET%TEMP.txt
if not exist TEMP.txt then
    del -q %MERLIN_DIR_SET%TEMP.txt
endif
if exist TEMP.txt then
    set MERLIN_DIR "fs0:" 
    set MERLIN_DIR_SET TRUE
    del -q TEMP.txt
endif

echo TEMP >> %DRG_POST_EXE_CMD%TEMP.txt
if not exist TEMP.txt then
    del -q %DRG_POST_EXE_CMD%TEMP.txt
endif
if exist TEMP.txt then
    set DRG_POST_EXE_CMD echo
endif 

echo TEMP >> %MERLIN_VAR_SET%TEMP.txt
if not exist TEMP.txt then
    del -q %MERLIN_VAR_SET%TEMP.txt
endif
if exist TEMP.txt then
    set MERLIN "MerlinX.efi" 
    set MERLIN_VAR_SET TRUE
    del -q TEMP.txt
endif
set MERLIN_COMMAND  "%MERLIN% %MERLIN_EXTRA%"
echo MERLIN COMMAND ==  %MERLIN_COMMAND%
echo "switching to drive %MERLIN_DRIVE%"
%MERLIN_DRIVE%
echo "CHANGING TO MERLINX DIR: %MERLIN_DIR%"
set ORIGINAL_CWD  %cwd%
cd %MERLIN_DIR%

if not exist %MERLIN% then
   set -d MERLIN_VAR_SET
   echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   echo !!!!! MERLINX is not FOUND          !!!!! 
   echo !!!!! MERLINX = %MERLIN%            !!!!! 
   echo !!!!! MERLIN_DRIVE = %MERLIN_DRIVE% !!!!! 
   echo !!!!! MERLIN_DIR = %MERLIN_DIR%     !!!!! 
   echo !!!!!                               !!!!! 
   echo !!!!!                               !!!!! 
   echo !!!!!                               !!!!! 
   echo !!!!! EXITING......                 !!!!! 
   echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   goto done
endif

echo TEMP >> %DRG_RESUME_REGRESSION%TEMP.txt 
if not exist TEMP.TXT then # %DRG_RESUME_REGRESSION% exists
    del -q %DRG_RESUME_REGRESSION%TEMP.txt
endif
if exist TEMP.TXT then
   set DRG_RESUME_REGRESSION 0
   del -q TEMP.txt
endif

echo TEMP >> %DRG_STOP_ON_FAIL%TEMP.txt
if not exist TEMP.TXT then
    del -q %DRG_STOP_ON_FAIL%TEMP.txt
endif
if exist TEMP.TXT then # DRG_STOP_ON_FAIL does not exist
    set DRG_STOP_ON_FAIL 0
   del -q TEMP.txt
endif

echo TEMP >> %DRG_RESET_ON_FAIL%TEMP.txt
if not exist TEMP.TXT then
    del -q %DRG_RESET_ON_FAIL%TEMP.txt
endif
if exist TEMP.TXT then # DRG_RESET_ON_FAIL does not exist
    set DRG_RESET_ON_FAIL 0
   del -q TEMP.txt
endif


echo TEMP >> %DRG_START_FRESH%TEMP.txt
if not exist TEMP.TXT then # DRG_START_FRESH exists
    if %DRG_START_FRESH% eq 1 then 
        echo DRG_START_FRESH is set. 
        echo   removing *.var, *.run *.hng fail.txt log.txt
        del -q %OBJ_DIR%\*.var
        del -q %OBJ_DIR%\*.run
        del -q %OBJ_DIR%\*.hng
        del -q %OBJ_DIR%\fail.txt
        del -q %OBJ_DIR%\log.txt
    endif
    del -q %DRG_START_FRESH%TEMP.txt
endif
if exist TEMP.TXT then # %DRG_START_FRESH% does not exist
   set DRG_START_FRESH 0
   del -q TEMP.txt
endif
set DRG_START_FRESH 0

echo TEMP >> %DRG_CURRENT_SEED_EXISTS%TEMP.txt
if not exist TEMP.TXT then # %DRG_CURRENT_SEED_EXISTS% exists
    del -q %DRG_CURRENT_SEED_EXISTS%TEMP.txt
endif
if exist TEMP.TXT then # %DRG_CURRENT_SEED_EXISTS% does not exist 
   set DRG_CURRENT_SEED NONE 
   set DRG_CURRENT_SEED_EXISTS 1 
   del -q TEMP.txt
endif

echo TEMP >> %VVAR2%TEMP.txt
if not exist TEMP.TXT then # %VVAR2% exists
   del -q %VVAR2%TEMP.txt
endif
if exist TEMP.TXT then # %VVAR2% does not exist
    echo VVAR2 env not set. Defaulting to Single Socket
    set VVAR2 "0x1000000"
    del -q TEMP.txt
endif

echo TEMP >> %VVAR3%TEMP.txt
if not exist TEMP.TXT then # %VVAR3% exists
    del -q %VVAR3%TEMP.txt
endif
if exist TEMP.TXT then # %VVAR3% does not exist
    echo VVAR3 env not set. Defaulting to Single Socket
    set VVAR3 "0x800000"
    del -q TEMP.txt
endif

echo TEMP >> %VVAR4%TEMP.txt
if not exist TEMP.TXT then # %VVAR4% exists
   del -q %VVAR4%TEMP.txt
endif
if exist TEMP.TXT then # %VVAR4% does not exist
    echo VVAR4 env not set. Defaulting to First ID
    set VVAR4 "0x0"
    del -q TEMP.txt
endif

echo TEMP >> %VVAR5%TEMP.txt
if not exist TEMP.TXT then # %VVAR5% exists
    del -q %VVAR5%TEMP.txt
endif
if exist TEMP.TXT then # %VVAR5% does not exist
    echo VVAR5 env not set. Defaulting to Second ID
    set VVAR5 "0x1"
    del -q TEMP.txt
endif

set VVAR "2 %VVAR2% 3 %VVAR3% 4 %VVAR4% 5 %VVAR5% %VVAR_EXTRA%"

echo TEMP >> %DRG_LOOP_FOREVER%TEMP.txt
if not  exist TEMP.TXT then # %DRG_LOOP_FOREVER% exists
    del -q %DRG_LOOP_FOREVER%TEMP.txt
endif
if exist TEMP.TXT then
   set DRG_LOOP_FOREVER 0
   del -q TEMP.txt
endif

if %1 eq "" then
    echo "NEED TO PASS DIRECTORY OF SEEDS IN arg1"
    echo "exiting...."
    goto done
endif



####### DONE SETTING UP VARIABLES 

echo Starting regression
echo ************** >> %OBJ_DIR%\fail.txt
:loop
if %DRG_RESUME_REGRESSION% == 1 then
    echo Resuming regression...
endif
for %n in %RE%.obj
    if %DRG_CURRENT_SEED_EXISTS% == 1 then
        if %n == %DRG_CURRENT_SEED% then
            if %DRG_RESUME_REGRESSION% == 1 then
                set DRG_RESUME_REGRESSION 0
                goto nextloop
            endif
        endif
    endif
    if %DRG_RESUME_REGRESSION% == 1 then
        echo skipping already run seed %n
        goto nextloop
    endif
    if exist %n.skp then
        goto nextloop
    endif
    if not exist %n then 
       echo %n not found!!!
       goto done
    endif 
    set DRG_CURRENT_SEED %n
    echo running "%MERLIN_COMMAND% -a %n -d %VVAR%"
    echo running "%MERLIN_COMMAND% -a %n -d %VVAR%" >> %OBJ_DIR%\log.txt
    echo running %n >> %n.hng 
    %MERLIN_COMMAND% -a %n -d %VVAR%
    rm %n.hng
    if exist %n.var then
        echo !!!!!!!!!!!!!!!! >> %OBJ_DIR%\fail.txt
        echo %n FAILED >> %OBJ_DIR%\fail.txt
        echo FOUND %n.var
        echo !!! %n FAILED !!!
        if %DRG_RESET_ON_FAIL% == 1 then
            echo !!! DRG_RESET_ON_FAIL is set... RESETTING SYSTEM !!!
            stall 3000000
            reset
        endif
        if %DRG_STOP_ON_FAIL% == 1 then
            echo !!! DRG_STOP_ON_FAIL is set. Stopping regression!!!
            goto done
        endif
        goto nextloop
    endif
    echo  %n PASSED >> %OBJ_DIR%\log.txt
    cat %OBJ_DIR%\fail.txt
    :nextloop
    %DRG_POST_EXE_CMD%
endfor
if %DRG_LOOP_FOREVER% == 1 then
    goto loop
endif
echo regression info in %OBJ_DIR%\log.txt
echo fail info in %OBJ_DIR%\fail.txt

:done
echo "CHANGING BACK TO DIR: %ORIGINAL_CWD%"
cd %ORIGINAL_CWD%\
