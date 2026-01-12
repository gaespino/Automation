echo -off

:external
if %1 eq "" then
    goto defaults
endif
if %2 eq "" then
    goto defaults
endif

set ulxpath %1
set ulxcpu %2

goto execute

:defaults
# =============================================================================
# DEFAULT VALUES
# =============================================================================

#  set ulxpath fs1:\EFI\ulx
# set ulxcpu GNR_B0

:execute
# =============================================================================
# ULX Execution
# =============================================================================

# %ulxpath%\ulx.efi -info %ulxpath%\ulx.ini -cpu %ulxcpu%
echo APIC Unlock will be performed using Merlin for DMR