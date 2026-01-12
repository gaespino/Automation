echo -off

:varchecks
# =============================================================================
# VARIABLES CHECK
# =============================================================================

if %1 eq "" then
    echo "ERROR: No valid CHOP configuration selected, use: GNR or CWF"
    goto end
endif

if %2 eq "" then
    echo "ERROR: Content Path empty"
    goto end
endiF

:config
# =============================================================================
# CONFIGURATION PARAMETERS
# =============================================================================

set SLICE_CHOP %1

# SLICE_CHOP as an external variable
# Placeholder in case we need to add product specific stuff

:external
# =============================================================================
# EXTERNAL PARAMETERS
# =============================================================================

echo " "
echo " Setting Content Path: %2"
echo " "

set CONTENT %2

:end