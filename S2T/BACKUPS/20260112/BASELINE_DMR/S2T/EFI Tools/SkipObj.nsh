# SkipObj.nsh "path\to\your\folder" "DL32-Blender-A1J-0F10001F"
# SkipObj.nsh

echo -off

set folder %1
set name_criteria %2

if not exist %folder% then
    echo Folder %folder% does not exist.
    goto done
endif

if %2 eq "" then
    echo criteria not set, need a criteria to move seeds to skip.
    goto done
endif

set obj_dir %folder%"\*%2*"

for %f in %obj_dir%
    if exist %f.obj then
        mv %f.obj %f.skp
    endif

    :nextloop
endfor

:done
