echo -off
if "%BASE_PATH%" == "" then
 set BASE_PATH %cwd%
endif

if "%REVERT_MOVE%" == "" then
 set REVERT_MOVE 0
endif

echo 
echo !! Base Folder: %BASE_PATH%
echo !! "Operation Mode: %REVERT_MOVE% (0:Normal - 1:Revert)"
echo

if "%1" == "" then
 echo Not valid path selected
 goto end
endif

if "%2" == "" then
 echo Not valid name selected
 goto end
endif

if "%3" == "revert" then
 echo Moving files back from SKIP_PATTERNS folder
 set REVERT_MOVE 1
endif

:move

if %REVERT_MOVE% == 1 then
 echo Performing Revert Operation moving files from SKIP_PATTERNS back to main folder
 cd %1
 if exist SKIP_PATTERNS then
  echo SKIP_PATTERNS folder found, processing files...
  cd SKIP_PATTERNS
  for %f in "*%2*"
   if exist %f then
    echo Moving back: %f
    mv %f ../%f
   endif
  endfor
  cd ..
  # Remove SKIP_PATTERNS folder if empty
  rmdir SKIP_PATTERNS 2>nul
  echo Revert operation complete
 else
  echo No SKIP_PATTERNS folder found in %1
 endif
else
 echo Performing Skip Operation - moving .obj files to SKIP_PATTERNS folder
 cd %1
 # Create SKIP_PATTERNS folder if it doesn't exist
 if not exist SKIP_PATTERNS then
  mkdir SKIP_PATTERNS
  echo Created SKIP_PATTERNS folder
 endif
 
 for %f in "*%2*".obj
  echo File: %f
   if exist %f then
    echo Moving: %f to SKIP_PATTERNS/%f
    mv %f SKIP_PATTERNS/%f
   endif
 endfor
endif

echo Operation Complete

:end
echo Returning to base path: %BASE_PATH%
cd %BASE_PATH%