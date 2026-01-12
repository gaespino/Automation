echo -off

if %1 eq "1" then
    echo "Dragon regression configured to Stop on Fail"
    set DRG_STOP_ON_FAIL 1
else
    set DRG_STOP_ON_FAIL 0
endif

:defaults
# =============================================================================
# DEFAULT VALUES
# =============================================================================

# Cannot be used with Framework for now
set DRG_START_FRESH 1
set DRG_RESUME_REGRESSION 0
set DRG_RESET_ON_FAIL 0
set DRG_LOOP_FOREVER 0

