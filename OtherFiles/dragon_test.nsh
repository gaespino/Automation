echo -off

############################################################
# NORMAL MODE
# All variables are defined in this script
############################################################

# Clean up VVAR variables
if "%VVAR0%" neq "" then
  echo "VVAR0 removed"
  set VVAR0 ""
else
  echo "VVAR0 not set"
endif
if "%VVAR1%" neq "" then
  echo "VVAR1 removed"
  set VVAR1 ""
else
  echo "VVAR1 not set"
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

set MERLIN_DIR "fs1:\EFI\Version8.15\BinFiles\Release"
set MERLIN "MerlinX.efi"
set OBJPATH "fs1:\content\Dragon\7410_0x0E_PPV_MM\GNR128C_H_1UP"

set DRG_STOP_ON_FAIL 1
set TEST_FAILED "false"

# Clean up any existing .var, .miss, and log.txt files
for %a in %OBJPATH%\*.var
  if exist %a then
    rm %a
  endif
endfor
for %a in %OBJPATH%\*.miss
  if exist %a then
    rm %a
  endif
endfor
if exist %OBJPATH%\log.txt then
  rm %OBJPATH%\log.txt
endif

set VVAR0 "0x04C4B40"
set VVAR1 "80064000"
set VVAR2 "0x1000000"
set VVAR3 "0x800000"
set VVARS "0 %VVAR0% 1 %VVAR1% 2 %VVAR2% 3 %VVAR3%"

## Seed 1 - DH10a-PPVIsaOn-0Demo-0E200017
set OBJFILE "DH10a-PPVIsaOn-0Demo-0E200017.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 2 - DH10a-PPVIsaOn-0Sanity-CST-0E20005D
set OBJFILE "DH10a-PPVIsaOn-0Sanity-CST-0E20005D.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 3 - DH10a-PPVIsaOn-0Sanity-ISA-0E20005E
set OBJFILE "DH10a-PPVIsaOn-0Sanity-ISA-0E20005E.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 4 - DH10a-PPVIsaOn-0Sanity-MEM-0E20005F
set OBJFILE "DH10a-PPVIsaOn-0Sanity-MEM-0E20005F.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 5 - DH10a-PPVIsaOn-0Sanity-MSR-0E200060
set OBJFILE "DH10a-PPVIsaOn-0Sanity-MSR-0E200060.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 6 - DH10a-PPVIsaOn-0Sanity-P23-0E200062
set OBJFILE "DH10a-PPVIsaOn-0Sanity-P23-0E200062.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 7 - DH10a-PPVIsaOn-0Sanity-PST-0E200063
set OBJFILE "DH10a-PPVIsaOn-0Sanity-PST-0E200063.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 8 - DH10a-PPVIsaOn-0Sanity-RNG-0E200064
set OBJFILE "DH10a-PPVIsaOn-0Sanity-RNG-0E200064.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 9 - DH10a-PPVIsaOn-0Sanity-TSC-0E20005B
set OBJFILE "DH10a-PPVIsaOn-0Sanity-TSC-0E20005B.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 10 - DH10a-PPVIsaOn-0Sanity-VMX-0E20005C
set OBJFILE "DH10a-PPVIsaOn-0Sanity-VMX-0E20005C.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 11 - DH10a-PPVIsaOn-0SanityPR-P-0E200066
set OBJFILE "DH10a-PPVIsaOn-0SanityPR-P-0E200066.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 12 - DH10a-PPVIsaOn-0SanityPR-V-0E200065
set OBJFILE "DH10a-PPVIsaOn-0SanityPR-V-0E200065.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 13 - DH10a-PPVIsaOn-0Sanity-UFS-0E220000
set OBJFILE "DH10a-PPVIsaOn-0Sanity-UFS-0E220000.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 14 - DH10a-PPVIsaOn-Skipper-Y-0E200075
set OBJFILE "DH10a-PPVIsaOn-Skipper-Y-0E200075.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 15 - DH10a-PPVIsaOn-Cayley-DIB-0E200004
set OBJFILE "DH10a-PPVIsaOn-Cayley-DIB-0E200004.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 16 - DH10a-PPVIsaOn-Skipper-Z-0E200076
set OBJFILE "DH10a-PPVIsaOn-Skipper-Z-0E200076.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 17 - DH10a-PPVIsaOn-Fireworx-Z-0E200024
set OBJFILE "DH10a-PPVIsaOn-Fireworx-Z-0E200024.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 18 - DH10a-PPVIsaOn-Cayley-DBFN-0E200005
set OBJFILE "DH10a-PPVIsaOn-Cayley-DBFN-0E200005.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 19 - DH10a-PPVIsaOn-1FireC-Z-0E200023
set OBJFILE "DH10a-PPVIsaOn-1FireC-Z-0E200023.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 20 - DH10a-PPVIsaOn-FRM-MMulSDZ-0E200038
set OBJFILE "DH10a-PPVIsaOn-FRM-MMulSDZ-0E200038.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 21 - DH10a-PPVIsaOn-1DittoC-GX-0E20001C
set OBJFILE "DH10a-PPVIsaOn-1DittoC-GX-0E20001C.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 22 - DH10a-PPVIsaOn-Frenzy-Z-0E200033
set OBJFILE "DH10a-PPVIsaOn-Frenzy-Z-0E200033.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 23 - DH10a-PPVIsaOn-PlusOne-Mhd-0E200058
set OBJFILE "DH10a-PPVIsaOn-PlusOne-Mhd-0E200058.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 24 - DH10a-PPVIsaOn-Frenzy-Z-0E20002C
set OBJFILE "DH10a-PPVIsaOn-Frenzy-Z-0E20002C.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 25 - DH10a-PPVIsaOn-1LeekC-X-0E200049
set OBJFILE "DH10a-PPVIsaOn-1LeekC-X-0E200049.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 26 - DH10a-PPVIsaOn-FRM-AddDZ-0E200040
set OBJFILE "DH10a-PPVIsaOn-FRM-AddDZ-0E200040.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 27 - DH10a-PPVIsaOn-DittoMT-CZ-0E20001E
set OBJFILE "DH10a-PPVIsaOn-DittoMT-CZ-0E20001E.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 28 - DH10a-PPVIsaOn-Fireworx-Z-0E200026
set OBJFILE "DH10a-PPVIsaOn-Fireworx-Z-0E200026.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 29 - DH10a-PPVIsaOn-FRM-CMultSZ-0E20003B
set OBJFILE "DH10a-PPVIsaOn-FRM-CMultSZ-0E20003B.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 30 - DH10a-PPVIsaOn-Aes-FZ-0E200001
set OBJFILE "DH10a-PPVIsaOn-Aes-FZ-0E200001.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 31 - DH10a-PPVIsaOn-Frenzy-Y-0E20002F
set OBJFILE "DH10a-PPVIsaOn-Frenzy-Y-0E20002F.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 32 - DH10a-PPVIsaOn-Aes-DZ-0E200000
set OBJFILE "DH10a-PPVIsaOn-Aes-DZ-0E200000.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 33 - DH10a-PPVIsaOn-Yakko-WsZ-0E20007E
set OBJFILE "DH10a-PPVIsaOn-Yakko-WsZ-0E20007E.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 34 - DH10a-PPVIsaOn-1Aught-B7AZ-0E200002
set OBJFILE "DH10a-PPVIsaOn-1Aught-B7AZ-0E200002.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 35 - DH10a-PPVIsaOn-1Loki-SM-0E200052
set OBJFILE "DH10a-PPVIsaOn-1Loki-SM-0E200052.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 36 - DH10a-PPVIsaOn-Twiddle-3Y-0E200079
set OBJFILE "DH10a-PPVIsaOn-Twiddle-3Y-0E200079.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 37 - DH10a-PPVIsaOn-FRM-MMulSSZ-0E20003D
set OBJFILE "DH10a-PPVIsaOn-FRM-MMulSSZ-0E20003D.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 38 - DH10a-PPVIsaOn-Yakko-WhZ-0E20007D
set OBJFILE "DH10a-PPVIsaOn-Yakko-WhZ-0E20007D.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 39 - DH10a-PPVIsaOn-Frenzy-Y-0E200034
set OBJFILE "DH10a-PPVIsaOn-Frenzy-Y-0E200034.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 40 - DH10a-PPVIsaOn-Cayley-DBFC-0E20000A
set OBJFILE "DH10a-PPVIsaOn-Cayley-DBFC-0E20000A.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 41 - DH10a-PPVIsaOn-DittoMT-CZ-0E20001F
set OBJFILE "DH10a-PPVIsaOn-DittoMT-CZ-0E20001F.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 42 - DH10a-PPVIsaOn-Frenzy-X-0E200030
set OBJFILE "DH10a-PPVIsaOn-Frenzy-X-0E200030.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 43 - DH10a-PPVIsaOn-LeekSpin-Y-0E20004E
set OBJFILE "DH10a-PPVIsaOn-LeekSpin-Y-0E20004E.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 44 - DH10a-PPVIsaOn-Cayley-WB1-0E200003
set OBJFILE "DH10a-PPVIsaOn-Cayley-WB1-0E200003.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 45 - DH10a-PPVIsaOn-LeekSpin-Y-0E20004B
set OBJFILE "DH10a-PPVIsaOn-LeekSpin-Y-0E20004B.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 46 - DH10a-PPVIsaOn-FRM-TranDZ-0E200039
set OBJFILE "DH10a-PPVIsaOn-FRM-TranDZ-0E200039.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 47 - DH10a-PPVIsaOn-Skipper-Y-0E200077
set OBJFILE "DH10a-PPVIsaOn-Skipper-Y-0E200077.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 48 - DH10a-PPVIsaOn-1Fissure-M-0E200028
set OBJFILE "DH10a-PPVIsaOn-1Fissure-M-0E200028.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 49 - DH10a-PPVIsaOn-Fireworx-Y-0E200025
set OBJFILE "DH10a-PPVIsaOn-Fireworx-Y-0E200025.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 50 - DH10a-PPVIsaOn-Yakko-WdZ-0E20007F
set OBJFILE "DH10a-PPVIsaOn-Yakko-WdZ-0E20007F.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 51 - DH10a-PPVIsaOn-Satsuma-Z-0E200068
set OBJFILE "DH10a-PPVIsaOn-Satsuma-Z-0E200068.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 52 - DH10a-PPVIsaOn-Scylla-SQFY-0E20006F
set OBJFILE "DH10a-PPVIsaOn-Scylla-SQFY-0E20006F.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 53 - DH10a-PPVIsaOn-Ditto-MACZ-0E20001B
set OBJFILE "DH10a-PPVIsaOn-Ditto-MACZ-0E20001B.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 54 - DH10a-PPVIsaOn-Flipper-0E20002A
set OBJFILE "DH10a-PPVIsaOn-Flipper-0E20002A.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 55 - DH10a-PPVIsaOn-1CayleyO-LS-0E20000E
set OBJFILE "DH10a-PPVIsaOn-1CayleyO-LS-0E20000E.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 56 - DH10a-PPVIsaOn-1FrenzyC-Z-0E200035
set OBJFILE "DH10a-PPVIsaOn-1FrenzyC-Z-0E200035.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 57 - DH10a-PPVIsaOn-Twiddle-Y-0E20007A
set OBJFILE "DH10a-PPVIsaOn-Twiddle-Y-0E20007A.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 58 - DH10a-PPVIsaOn-Yakko-WsZ-0E20007B
set OBJFILE "DH10a-PPVIsaOn-Yakko-WsZ-0E20007B.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 59 - DH10a-PPVIsaOn-1CayleyO-VT-0E200011
set OBJFILE "DH10a-PPVIsaOn-1CayleyO-VT-0E200011.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 60 - DH10a-PPVIsaOn-Frenzy-Z-0E200032
set OBJFILE "DH10a-PPVIsaOn-Frenzy-Z-0E200032.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 61 - DH10a-PPVIsaOn-Cayley-DIB-0E200009
set OBJFILE "DH10a-PPVIsaOn-Cayley-DIB-0E200009.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 62 - DH10a-PPVIsaOn-Cayley-DHC-0E20000B
set OBJFILE "DH10a-PPVIsaOn-Cayley-DHC-0E20000B.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 63 - DH10a-PPVIsaOn-Frenzy-Z-0E20002D
set OBJFILE "DH10a-PPVIsaOn-Frenzy-Z-0E20002D.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 64 - DH10a-PPVIsaOn-1DittoC-Z-0E20001D
set OBJFILE "DH10a-PPVIsaOn-1DittoC-Z-0E20001D.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 65 - DH10a-PPVIsaOn-1LeekC-Y-0E200048
set OBJFILE "DH10a-PPVIsaOn-1LeekC-Y-0E200048.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 66 - DH10a-PPVIsaOn-1Loki-PM-0E200051
set OBJFILE "DH10a-PPVIsaOn-1Loki-PM-0E200051.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 67 - DH10a-PPVIsaOn-Yakko-WdZ-0E20007C
set OBJFILE "DH10a-PPVIsaOn-Yakko-WdZ-0E20007C.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 68 - DH10a-PPVIsaOn-FRM-CMultHZ-0E20003F
set OBJFILE "DH10a-PPVIsaOn-FRM-CMultHZ-0E20003F.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 69 - DH10a-PPVIsaOn-LeekSpin-X-0E20004F
set OBJFILE "DH10a-PPVIsaOn-LeekSpin-X-0E20004F.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 70 - DH10a-PPVIsaOn-Satsuma-Z-0E200067
set OBJFILE "DH10a-PPVIsaOn-Satsuma-Z-0E200067.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 71 - DH10a-PPVIsaOn-Ditto-GCAG-0E200018
set OBJFILE "DH10a-PPVIsaOn-Ditto-GCAG-0E200018.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 72 - DH10a-PPVIsaOn-Flipper-0E200029
set OBJFILE "DH10a-PPVIsaOn-Flipper-0E200029.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 73 - DH10a-PPVIsaOn-PlusOne-Mhs-0E200059
set OBJFILE "DH10a-PPVIsaOn-PlusOne-Mhs-0E200059.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 74 - DH10a-PPVIsaOn-Frenzy-X-0E20002B
set OBJFILE "DH10a-PPVIsaOn-Frenzy-X-0E20002B.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 75 - DH10a-PPVIsaOn-Scylla-QCZ-0E200071
set OBJFILE "DH10a-PPVIsaOn-Scylla-QCZ-0E200071.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 76 - DH10a-PPVIsaOn-1CayleyC-0E20000D
set OBJFILE "DH10a-PPVIsaOn-1CayleyC-0E20000D.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 77 - DH10a-PPVIsaOn-1FireC-Y-0E200021
set OBJFILE "DH10a-PPVIsaOn-1FireC-Y-0E200021.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 78 - DH10a-PPVIsaOn-1LeekC-Z-0E20004A
set OBJFILE "DH10a-PPVIsaOn-1LeekC-Z-0E20004A.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 79 - DH10a-PPVIsaOn-FRM-TranSZ-0E20003E
set OBJFILE "DH10a-PPVIsaOn-FRM-TranSZ-0E20003E.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 80 - DH10a-PPVIsaOn-Fuso-0E200044
set OBJFILE "DH10a-PPVIsaOn-Fuso-0E200044.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 81 - DH10a-PPVIsaOn-1FrenzyC-X-0E200037
set OBJFILE "DH10a-PPVIsaOn-1FrenzyC-X-0E200037.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 82 - DH10a-PPVIsaOn-Cayley-WJ-0E20000C
set OBJFILE "DH10a-PPVIsaOn-Cayley-WJ-0E20000C.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 83 - DH10a-PPVIsaOn-FRM-CvtIHZ-0E20003A
set OBJFILE "DH10a-PPVIsaOn-FRM-CvtIHZ-0E20003A.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 84 - DH10a-PPVIsaOn-Scylla-QCZ-0E20006B
set OBJFILE "DH10a-PPVIsaOn-Scylla-QCZ-0E20006B.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 85 - DH10a-PPVIsaOn-Scylla-SQCZ-0E20006D
set OBJFILE "DH10a-PPVIsaOn-Scylla-SQCZ-0E20006D.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 86 - DH10a-PPVIsaOn-1Eclipse-0E200020
set OBJFILE "DH10a-PPVIsaOn-1Eclipse-0E200020.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 87 - DH10a-PPVIsaOn-1FireC-X-0E200022
set OBJFILE "DH10a-PPVIsaOn-1FireC-X-0E200022.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 88 - DH10a-PPVIsaOn-1FrenzyC-Y-0E200036
set OBJFILE "DH10a-PPVIsaOn-1FrenzyC-Y-0E200036.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 89 - DH10a-PPVIsaOn-1Loki-MM-0E200053
set OBJFILE "DH10a-PPVIsaOn-1Loki-MM-0E200053.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 90 - DH10a-PPVIsaOn-Ditto-MAAZ-0E200019
set OBJFILE "DH10a-PPVIsaOn-Ditto-MAAZ-0E200019.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 91 - DH10a-PPVIsaOn-LeekSpin-X-0E20004C
set OBJFILE "DH10a-PPVIsaOn-LeekSpin-X-0E20004C.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 92 - DH10a-PPVIsaOn-FRM-SqrtSZ-0E20003C
set OBJFILE "DH10a-PPVIsaOn-FRM-SqrtSZ-0E20003C.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 93 - DH10a-PPVIsaOn-LeekSpin-Z-0E20004D
set OBJFILE "DH10a-PPVIsaOn-LeekSpin-Z-0E20004D.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 94 - DH10a-PPVIsaOn-1CayleyO-VB-0E200012
set OBJFILE "DH10a-PPVIsaOn-1CayleyO-VB-0E200012.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 95 - DH10a-PPVIsaOn-1FRMC-Z-0E200042
set OBJFILE "DH10a-PPVIsaOn-1FRMC-Z-0E200042.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 96 - DH10a-PPVIsaOn-Cayley-DHN-0E200006
set OBJFILE "DH10a-PPVIsaOn-Cayley-DHN-0E200006.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 97 - DH10a-PPVIsaOn-Kawachi-0E200047
set OBJFILE "DH10a-PPVIsaOn-Kawachi-0E200047.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 98 - DH10a-PPVIsaOn-LeekSpin-Z-0E200050
set OBJFILE "DH10a-PPVIsaOn-LeekSpin-Z-0E200050.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 99 - DH10a-PPVIsaOn-Oakley-RarX-0E200057
set OBJFILE "DH10a-PPVIsaOn-Oakley-RarX-0E200057.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 100 - DH10a-PPVIsaOn-Scylla-QFZ-0E20006A
set OBJFILE "DH10a-PPVIsaOn-Scylla-QFZ-0E20006A.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 101 - DH10a-PPVIsaOn-Scylla-QFZ-0E200070
set OBJFILE "DH10a-PPVIsaOn-Scylla-QFZ-0E200070.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 102 - DH10a-PPVIsaOn-Scylla-SQFZ-0E200072
set OBJFILE "DH10a-PPVIsaOn-Scylla-SQFZ-0E200072.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 103 - DH10a-PPVIsaOn-Ditto-GCCG-0E20001A
set OBJFILE "DH10a-PPVIsaOn-Ditto-GCCG-0E20001A.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 104 - DH10a-PPVIsaOn-Scylla-SQCZ-0E200073
set OBJFILE "DH10a-PPVIsaOn-Scylla-SQCZ-0E200073.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 105 - DH10a-PPVIsaOn-1Charyb-QCZ-0E200013
set OBJFILE "DH10a-PPVIsaOn-1Charyb-QCZ-0E200013.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 106 - DH10a-PPVIsaOn-1Charyb-QFY-0E200015
set OBJFILE "DH10a-PPVIsaOn-1Charyb-QFY-0E200015.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 107 - DH10a-PPVIsaOn-Frenzy-Z-0E20002E
set OBJFILE "DH10a-PPVIsaOn-Frenzy-Z-0E20002E.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 108 - DH10a-PPVIsaOn-Frenzy-Z-0E200031
set OBJFILE "DH10a-PPVIsaOn-Frenzy-Z-0E200031.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 109 - DH10a-PPVIsaOn-Millet-CG-0E200054
set OBJFILE "DH10a-PPVIsaOn-Millet-CG-0E200054.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 110 - DH10a-PPVIsaOn-Scylla-SQFX-0E20006E
set OBJFILE "DH10a-PPVIsaOn-Scylla-SQFX-0E20006E.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 111 - DH10a-PPVIsaOn-0Sanity-TRB-0E230000
set OBJFILE "DH10a-PPVIsaOn-0Sanity-TRB-0E230000.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 112 - DH10a-PPVIsaOn-0Sanity-MUC-0E200061
set OBJFILE "DH10a-PPVIsaOn-0Sanity-MUC-0E200061.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 113 - DH10a-PPVIsaOn-0Sanity-TRB-0E110000
set OBJFILE "DH10a-PPVIsaOn-0Sanity-TRB-0E110000.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 114 - DH10a-PPVIsaOn-1CayleyO-VI-0E20000F
set OBJFILE "DH10a-PPVIsaOn-1CayleyO-VI-0E20000F.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 115 - DH10a-PPVIsaOn-Oakley-LegX-0E200056
set OBJFILE "DH10a-PPVIsaOn-Oakley-LegX-0E200056.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 116 - DH10a-PPVIsaOn-FRM-DivDZ-0E200041
set OBJFILE "DH10a-PPVIsaOn-FRM-DivDZ-0E200041.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 117 - DH10a-PPVIsaOn-Skipper-Z-0E200078
set OBJFILE "DH10a-PPVIsaOn-Skipper-Z-0E200078.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 118 - DH10a-PPVIsaOn-Cayley-WI-0E200007
set OBJFILE "DH10a-PPVIsaOn-Cayley-WI-0E200007.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 119 - DH10a-PPVIsaOn-1Charyb-QFX-0E200014
set OBJFILE "DH10a-PPVIsaOn-1Charyb-QFX-0E200014.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 120 - DH10a-PPVIsaOn-Scylla-SQFZ-0E20006C
set OBJFILE "DH10a-PPVIsaOn-Scylla-SQFZ-0E20006C.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 121 - DH10a-PPVIsaOn-Scylla-QFX-0E200074
set OBJFILE "DH10a-PPVIsaOn-Scylla-QFX-0E200074.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 122 - DH10a-PPVIsaOn-Fireworx-Y-0E200027
set OBJFILE "DH10a-PPVIsaOn-Fireworx-Y-0E200027.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 123 - DH10a-PPVIsaOn-Scylla-QFY-0E200069
set OBJFILE "DH10a-PPVIsaOn-Scylla-QFY-0E200069.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 124 - DH10a-PPVIsaOn-Cayley-WT1-0E200008
set OBJFILE "DH10a-PPVIsaOn-Cayley-WT1-0E200008.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 125 - DH10a-PPVIsaOn-1Charyb-QFZ-0E200016
set OBJFILE "DH10a-PPVIsaOn-1Charyb-QFZ-0E200016.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 126 - DH10a-PPVIsaOn-1Geode-RF-0E200045
set OBJFILE "DH10a-PPVIsaOn-1Geode-RF-0E200045.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 127 - DH10a-PPVIsaOn-Millet-RG-0E200055
set OBJFILE "DH10a-PPVIsaOn-Millet-RG-0E200055.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 128 - DH10a-PPVIsaOn-Kawachi-0E200046
set OBJFILE "DH10a-PPVIsaOn-Kawachi-0E200046.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 129 - DH10a-PPVIsaOn-Fuso-0E200043
set OBJFILE "DH10a-PPVIsaOn-Fuso-0E200043.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

## Seed 130 - DH10a-PPVIsaOn-1CayleyO-VJ-0E200010
set OBJFILE "DH10a-PPVIsaOn-1CayleyO-VJ-0E200010.obj"
if exist %OBJPATH%\%OBJFILE% then
  echo " Running %OBJFILE%"
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS% "
  echo "Running %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%" >> %OBJPATH%\log.txt
  %MERLIN_DIR%\%MERLIN% -a %OBJPATH%\%OBJFILE% -d %VVARS%
else
  echo "%OBJFILE% not found" >> %OBJPATH%\missing.miss
endif

# Check for .var file indicating failure
if exist %OBJPATH%\%OBJFILE%.var then
  echo "Failure detected: %OBJFILE%.var"
  set TEST_FAILED "true"
  if %DRG_STOP_ON_FAIL% eq 1 then
    goto END
  endif
endif

:END
# Display missing files if any
if exist %OBJPATH%\missing.miss then
  echo ""
  echo "==============================================="
  echo "Missing .obj files:"
  echo "==============================================="
  type %OBJPATH%\missing.miss
  echo "==============================================="
  echo ""
endif

if "%TEST_FAILED%" == "true" then
  echo "Test Failed"
else
  echo "Test Complete"
endif
