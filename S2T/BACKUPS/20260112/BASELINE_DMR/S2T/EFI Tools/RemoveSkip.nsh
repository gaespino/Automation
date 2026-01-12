# RemoveSkip.nsh "path\to\your\folder"
# RemoveSkip.nsh

echo -off
set folder %1

if not exist "%folder%" then
    echo Folder "%folder%" does not exist.
    goto done
endif
set obj_dir %folder%"\*"

for %f in %set obj%
    if exist %f.skp then
        mv %f.skp %f.obj
    endif
endfor

:done