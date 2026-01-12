echo -off
for %d in 0 1 2 3 4 5 6 7 8 9
    echo Checking for EFI folder on fs%d ...
    if exist fs%d:\EFI\runregression.nsh then
        echo Found EFI folder; setting fs%d:\ as working directory.
        fs%d:
        goto launchrtm
    endif
endfor
goto Error
 
:launchrtm
PpvReserveTestMem.efi 0x100000 0x43f00
cd EFI
goto Done
 
:Error
echo Could not find EFI Folder on any mounted drives!
 
:Done