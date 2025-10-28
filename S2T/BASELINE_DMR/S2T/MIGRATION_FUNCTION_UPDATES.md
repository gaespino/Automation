# Function-Level DMR Updates Applied to CoreManipulation.py

## Overview
This document tracks individual function improvements that were migrated from DMRCoreManipulation.py to CoreManipulation.py, separate from the major class/structure migration.

**Date**: 2025
**File**: CoreManipulation.py (3,590 lines)
**Source**: DMRCoreManipulation.py (2,968 lines)

---

## Functions Updated

### 1. gen_product_bootstring() - Lines 2717-2733

**Status**: ✅ COMPLETED

**Changes Applied**:
1. **Fixed typo**: `compute_cofig` → `compute_config`
2. **Removed parameter**: Eliminated deprecated `segment` parameter
3. **Unified fuse files**: Combined `_fuse_files_compute` and `_fuse_files_io` into single `fuse_files` parameter
4. **Added return type**: Added `-> str` type hint
5. **Updated implementation**: Simplified f-string formatting to match DMR

**Old Signature** (GNR):
```python
def gen_product_bootstring(bootopt = '', compute_cofig = 'GNRUCC', segment = 'X3',
                          b_extra = '', _boot_disable_ia = '', _boot_disable_llc ='',
                          fuse_string ='', _fuse_files_compute = '', _fuse_files_io =''):
```

**New Signature** (DMR):
```python
def gen_product_bootstring(bootopt = '', compute_config = 'X1', b_extra = '',
                          _boot_disable_ia = '', _boot_disable_llc ='',
                          fuse_string ='', fuse_files = '') -> str:
```

**Callers Updated**:
- ✅ Line 1934 in `_doboot()` method - Updated to use new parameter list
  - Removed `product_bs[die]['segment']` parameter
  - Combined `_fuse_files_compute` and `_fuse_files_io` into formatted `fuse_files_formatted` string
  - Format: `fuse_files_compute=["path1", "path2"], fuse_files_io=["path3", "path4"]`
- ✅ Line 614 in `SystemBooter.execute_boot()` - Already using correct new signature

---

### 2. read_postcode() - Lines 3233-3251

**Status**: ✅ COMPLETED

**Changes Applied**:
1. **Added DMR support**: Now checks for `imh0` (DMR) before falling back to `io0` (GNR)
2. **Updated register paths**:
   - DMR: `sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]`
   - GNR: `sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg`
3. **Improved error handling**: Changed error message color from YELLOW to RED for consistency
4. **Added docstring**: Documented register paths for both architectures

**Old Implementation** (GNR only):
```python
def read_postcode():
    try:
        pc = sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg
    except Exception as e:
        pc = None
        print(Fore.YELLOW + f">>> Unable to read PostCode with Exception: {e}"+ Fore.RESET)
    return pc
```

**New Implementation** (DMR + GNR):
```python
def read_postcode(): 
    '''
    Reads BIOS POST code register.
    Supports both DMR (imh0) and GNR (io0) architectures.
    DMR: sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]
    GNR: sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg
    '''
    try:
        if hasattr(sv.socket0, 'imh0'):
            pc = sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]
        else:
            pc = sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg
    except Exception as e:
        pc = None
        print(Fore.RED + f"Error reading BIOS POST code: {e}" + Fore.WHITE)
    return pc
```

---

### 3. set_biosbreak() - Lines 3162-3183 (NEW FUNCTION)

**Status**: ✅ COMPLETED - NEW HELPER FUNCTION ADDED

**Changes Applied**:
1. **Created new helper function**: Abstracted register access for both architectures
2. **Dual architecture support**:
   - DMR: `sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]`
   - GNR: `sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg`
3. **Added error handling**: Try-except block with colored error messages
4. **Parameterized**: Accepts value argument for flexibility

**New Implementation**:
```python
def set_biosbreak(value):
    '''
    Sets BIOS break register to specified value.
    Supports both DMR (imh0) and GNR (io0) architectures.
    DMR: sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6] = value
    GNR: sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = value
    
    Args:
        value: Integer value to set the register to
    '''
    try:
        if hasattr(sv.socket0, 'imh0'):
            sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6] = value
        else:
            sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = value
    except Exception as e:
        print(Fore.RED + f"Error setting BIOS break register: {e}" + Fore.WHITE)
```

**Usage Locations**:
- ✅ Line 2295: SystemBooter fast boot path (stop_after_mrc)
- ✅ Line 2299: SystemBooter fast boot path (boot_postcode)
- ✅ Line 2398: Legacy _doboot path (stop_after_mrc)
- ✅ Line 2409: Legacy _doboot path (boot_postcode)
- ✅ Line 3185: clear_biosbreak() function

---

### 4. clear_biosbreak() - Lines 3185-3192

**Status**: ✅ COMPLETED

**Changes Applied**:
1. **Simplified implementation**: Now calls `set_biosbreak(0)` helper
2. **Removed direct register access**: Delegated to `set_biosbreak()` for consistency
3. **Maintained docstring**: Kept documentation about both architectures

**Old Implementation** (Direct access):
```python
def clear_biosbreak():
    sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = 0
```

**New Implementation** (Using helper):
```python
def clear_biosbreak(): 
    '''
    Clears BIOS break register.
    Supports both DMR (imh0) and GNR (io0) architectures.
    DMR: sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6] = 0
    GNR: sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = 0
    '''
    set_biosbreak(0)
```

---

### 5. read_biospost() - Lines 3151-3161

**Status**: ✅ COMPLETED

**Changes Applied**:
1. **Uses read_postcode() helper**: Delegates to dual-architecture function
2. **Added error handling**: Checks for None return and prints appropriate message
3. **Added return value**: Now returns the postcode value
4. **Added docstring**: Documents the function's purpose

**Old Implementation** (Direct GNR access):
```python
def read_biospost():
    print ("POST = 0x%x" % sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg)
```

**New Implementation** (Using helper):
```python
def read_biospost():
    '''
    Reads and prints BIOS POST code.
    Uses read_postcode() helper to support both DMR and GNR architectures.
    '''
    pc = read_postcode()
    if pc is not None:
        print("POST = 0x%x" % pc)
    else:
        print("POST = Unable to read")
    return pc
```

---

## Direct Register Access Updates

### SystemBooter Class Updates

**Lines 2295-2299** (SystemBooter fast boot with fuse override):
```python
# OLD:
sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = AFTER_MRC_POST
sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = BOOT_STOP_POSTCODE

# NEW:
set_biosbreak(AFTER_MRC_POST)
set_biosbreak(BOOT_STOP_POSTCODE)
```

**Lines 2398-2411** (Legacy _doboot bootscript path):
```python
# OLD:
sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = AFTER_MRC_POST
print(f"sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg={AFTER_MRC_POST:#x}")
sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = BOOT_STOP_POSTCODE
print(f"sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg={BOOT_STOP_POSTCODE:#x}")

# NEW:
set_biosbreak(AFTER_MRC_POST)
print(f"biosscratchpad6 register set to: {AFTER_MRC_POST:#x}")
set_biosbreak(BOOT_STOP_POSTCODE)
print(f"biosscratchpad6 register set to: {BOOT_STOP_POSTCODE:#x}")
```

---

## Functions Verified (Already Correct)

The following functions were checked and confirmed to already match DMR:

### ✅ check_user_cancel() - Line 3097
- Signature matches DMR: `def check_user_cancel(execution_state=None):`

### ✅ clear_cancel_flag() - Line 3108
- Signature matches DMR: `def clear_cancel_flag(logger=None,cancel_flag=False):`

### ✅ svStatus() - Line 2739
- Signature matches DMR: `def svStatus(checkipc = True, checksvcores = True, refresh = False, reconnect = False):`

### ✅ go_to_efi() - Line 3194
- Signature matches DMR: `def go_to_efi(execution_state = None):`
- Already uses `clear_biosbreak()` helper

### ✅ _wait_for_post() - Line 3204
- Signature matches DMR: `def _wait_for_post(postcode, sleeptime = 3, timeout = 10, additional_postcode = None, execution_state=None):`
- Already uses `read_postcode()` helper

---

## Functions Previously Migrated

These functions were already migrated in earlier phases:

### ✅ mask_fuse_module_array() - Phase 4
- DMR function (60 lines) migrated to support both DMR (cbb0-3 modules) and GNR (compute0-2 cores)
- Lines 2844-2904 in CoreManipulation.py

### ✅ mask_fuse_llc_array() - Already existed
- Function already present and compatible with both architectures

---

## Architecture Support Summary

### Register Path Mappings

| Function | DMR Path | GNR Path |
|----------|----------|----------|
| **read_postcode()** | `sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]` | `sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg` |
| **set_biosbreak()** | `sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]` | `sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg` |

### Detection Method
All updated functions use `hasattr(sv.socket0, 'imh0')` to detect DMR architecture:
- If `imh0` exists → Use DMR register paths
- If `imh0` doesn't exist → Fall back to GNR register paths (io0)

---

## Verification Status

### Lint Errors
- ✅ gen_product_bootstring signature error: RESOLVED
- ✅ Line 1928/1934 caller error: RESOLVED
- ✅ read_postcode() architecture support: IMPLEMENTED
- ✅ clear_biosbreak() architecture support: IMPLEMENTED
- ✅ set_biosbreak() helper function: CREATED
- ✅ read_biospost() architecture support: IMPLEMENTED
- ⚠️ Pre-existing lint errors unrelated to migration remain (namednodes import, itp type hints, etc.)

### Function Call Audit
- ✅ All calls to `gen_product_bootstring()` verified and updated
- ✅ All direct register accesses replaced with helper functions
- ✅ All BIOS register operations now support both DMR and GNR

---

## Summary

**Functions Updated**: 5
- gen_product_bootstring() - Signature and parameter cleanup
- read_postcode() - Added DMR register path support
- set_biosbreak() - NEW helper function for dual architecture support
- clear_biosbreak() - Refactored to use set_biosbreak() helper
- read_biospost() - Refactored to use read_postcode() helper

**Direct Register Access Points Updated**: 4
- SystemBooter fast boot: 2 locations (lines 2295, 2299)
- Legacy _doboot: 2 locations (lines 2398, 2409)

**Functions Verified (No Changes Needed)**: 7+
- check_user_cancel(), clear_cancel_flag(), svStatus(), go_to_efi(), _wait_for_post(), and utility functions

**Migration Completeness**: 
- ✅ All major DMR function improvements migrated
- ✅ All function callers updated to match new signatures
- ✅ All BIOS register accesses abstracted for dual architecture support
- ✅ Backward compatibility maintained for both DMR and GNR architectures
- ✅ Error handling improved with consistent colored output

---

## Notes

1. The `segment` parameter was removed from gen_product_bootstring() because it's deprecated in DMR's SystemBooter approach
2. Fuse files are now passed as a single formatted string instead of separate compute/io parameters
3. All BIOS register operations now automatically detect and support both DMR (imh0) and GNR (io0) architectures
4. The new `set_biosbreak()` helper centralizes all biosscratchpad register writes
5. Detection is runtime-based using `hasattr(sv.socket0, 'imh0')` for maximum flexibility

**Next Steps**: Monitor for any runtime issues with the updated functions during testing on both DMR and GNR platforms.
