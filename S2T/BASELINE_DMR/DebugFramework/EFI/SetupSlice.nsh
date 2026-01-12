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
    echo "ERROR: No valid APIC DIE configuration selected -- CBB Number"
    goto end
endif

if %3 eq "" then
    echo "ERROR: No valid APIC DIE configuration selected -- Module Reference"
    goto end
endif

if %4 eq "" then
    echo "ERROR: Content Path empty"
    goto end
endiF

:config
# =============================================================================
# CONFIGURATION PARAMETERS
# =============================================================================

set SLICE_CHOP %1

# SLICE_CHOP as an external variable
# set SLICE_CHOP DMR

if %SLICE_CHOP% eq "DMR" then
	if %2 eq "0" then
		set CBB_0_APIC0 0x0
		set CBB_0_APIC1 0x2
		set CBB_1_APIC0 0x8
		set CBB_1_APIC1 0xa
		set CBB_2_APIC0 0x10
		set CBB_2_APIC1 0x12
		set CBB_3_APIC0 0x18
		set CBB_3_APIC1 0x1a
		set CBB_4_APIC0 0x20
		set CBB_4_APIC1 0x22
		set CBB_5_APIC0 0x28
		set CBB_5_APIC1 0x2a
		set CBB_6_APIC0 0x30
		set CBB_6_APIC1 0x32
		set CBB_7_APIC0 0x38
		set CBB_7_APIC1 0x3a
	endif
	if %2 eq "1" then
		set CBB_0_APIC0 0x100
		set CBB_0_APIC1 0x102
		set CBB_1_APIC0 0x108
		set CBB_1_APIC1 0x10a
		set CBB_2_APIC0 0x110
		set CBB_2_APIC1 0x112
		set CBB_3_APIC0 0x118
		set CBB_3_APIC1 0x11a
		set CBB_4_APIC0 0x120
		set CBB_4_APIC1 0x122
		set CBB_5_APIC0 0x128
		set CBB_5_APIC1 0x12a
		set CBB_6_APIC0 0x130
		set CBB_6_APIC1 0x132
		set CBB_7_APIC0 0x138
		set CBB_7_APIC1 0x13a
	endif
	if %2 eq "3" then
		set CBB_0_APIC0 0x200
		set CBB_0_APIC1 0x202
		set CBB_1_APIC0 0x208
		set CBB_1_APIC1 0x20a
		set CBB_2_APIC0 0x210
		set CBB_2_APIC1 0x212
		set CBB_3_APIC0 0x218
		set CBB_3_APIC1 0x21a
		set CBB_4_APIC0 0x220
		set CBB_4_APIC1 0x222
		set CBB_5_APIC0 0x228
		set CBB_5_APIC1 0x22a
		set CBB_6_APIC0 0x230
		set CBB_6_APIC1 0x232
		set CBB_7_APIC0 0x238
		set CBB_7_APIC1 0x23a
	endif
	if %2 eq "4" then
		set CBB_0_APIC0 0x300
		set CBB_0_APIC1 0x302
		set CBB_1_APIC0 0x308
		set CBB_1_APIC1 0x30a
		set CBB_2_APIC0 0x310
		set CBB_2_APIC1 0x312
		set CBB_3_APIC0 0x318
		set CBB_3_APIC1 0x31a
		set CBB_4_APIC0 0x320
		set CBB_4_APIC1 0x322
		set CBB_5_APIC0 0x328
		set CBB_5_APIC1 0x32a
		set CBB_6_APIC0 0x330
		set CBB_6_APIC1 0x332
		set CBB_7_APIC0 0x338
		set CBB_7_APIC1 0x33a
	endif
    goto external
endif

# More Products below this line

# If not any of the above exit
echo "ERROR: No valid CHOP configuration selected, use: DMR"
goto end

:external
# =============================================================================
# EXTERNAL PARAMETERS
# =============================================================================

echo " "
echo " Setting SLICE APIC Configuration for --> CHOP: %1, CBB: %2"
echo " "

if %3 eq "0" then
    set VVAR4 %CBB_0_APIC0%
    set VVAR5 %CBB_0_APIC1%
    goto setapic
endif

if %3 eq "1" then
    set VVAR4 %CBB_1_APIC0%
    set VVAR5 %CBB_1_APIC1%
    goto setapic
endif

if %3 eq "2" then
    set VVAR4 %CBB_2_APIC0%
    set VVAR5 %CBB_2_APIC1%
    goto setapic
endif

if %3 eq "3" then
    set VVAR4 %CBB_3_APIC0%
    set VVAR5 %CBB_3_APIC1%
    goto setapic
endif

if %3 eq "4" then
    set VVAR4 %CBB_4_APIC0%
    set VVAR5 %CBB_4_APIC1%
    goto setapic
endif

if %3 eq "5" then
    set VVAR4 %CBB_5_APIC0%
    set VVAR5 %CBB_5_APIC1%
    goto setapic
endif

if %3 eq "6" then
    set VVAR4 %CBB_6_APIC0%
    set VVAR5 %CBB_6_APIC1%
    goto setapic
endif

if %3 eq "7" then
    set VVAR4 %CBB_7_APIC0%
    set VVAR5 %CBB_7_APIC1%
    goto setapic
endif

# If any other value present, only set content
echo " Not Setting APICs used value is not available --> %2 -- %3"
goto setcontent

:setapic
echo " Setting Content Path: %4"
echo " VVAR4 set to: %VVAR4%"
echo " VVAR5 set to: %VVAR5%"
echo " "

:setcontent
set CONTENT %4

:end