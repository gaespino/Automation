# DMR Core Manipulation to Core Manipulation Migration Analysis

## Overview
This document compares `DMRCoreManipulation.py` (draft/DMR-specific) with `CoreManipulation.py` (main/GNR-specific) to identify:
1. Functions that exist in DMR but not in CoreManipulation
2. Functions that have updated logic in DMR
3. Recommended migration actions

---

## File Structure Comparison

### Version Information
- **DMRCoreManipulation.py**: Version 1.7 (3/7/2025) - DMR Initial Release, Matches CWF Functionality
- **CoreManipulation.py**: Version 1.6 (3/7/2025) - Enhanced with EFI, MRC, BIOS break variables

---

## Key Architectural Differences

### 1. **DMR vs GNR Naming Conventions**
| DMR Term | GNR Term | Description |
|----------|----------|-------------|
| `cbb` (Compute Building Block) | `compute` | Main compute die/tile |
| `imh` (IO Module Hub) | `io` | IO die/tile |
| `module` | `core` | Processing unit |
| `TOTAL_MODULES_PER_CBB` | `MAXPHYSICAL` | Max modules per compute |
| `TOTAL_ACTIVE_MODULES_PER_CBB` | `MAXLOGICAL` | Active/logical modules |

### 2. **Import Differences**
**DMR-specific:**
```python
import itpii
from typing import Dict, List, Optional, Union
```

**GNR-specific:**
```python
# No itpii import
# No typing imports
```

### 3. **Architecture Constants**
**DMR adds:**
```python
TOTAL_MODULES_PER_CBB = LoadConfig.MODS_PER_CBB
TOTAL_MODULES_PER_COMPUTE = LoadConfig.MODS_PER_COMPUTE
TOTAL_ACTIVE_MODULES_PER_CBB = LoadConfig.MODS_ACTIVE_PER_CBB
TOTAL_CBBS = LoadConfig.MAX_CBBS
TOTAL_IMHS = LoadConfig.MAX_IMHS
```

### 4. **Global Variables**
**DMR has additional frequency globals:**
```python
global_ia_fw_p1, global_ia_fw_pn, global_ia_fw_pm
global_ia_fw_pboot, global_ia_fw_pturbo, global_ia_vf_curves
global_ia_imh_p1, global_ia_imh_pn, global_ia_imh_pm, global_ia_imh_pturbo
global_cfc_fw_p0, global_cfc_fw_p1, global_cfc_fw_pm
global_cfc_cbb_p0, global_cfc_cbb_p1, global_cfc_cbb_pm
global_cfc_io_p0, global_cfc_io_p1, global_cfc_io_pm
global_cfc_mem_p0, global_cfc_mem_p1, global_cfc_mem_pm
global_1CPM_dis  # Addition not in GNR
global_fixed_mlc_volt  # Addition not in GNR
```

**GNR uses simpler structure:**
```python
global_ia_p0, global_ia_p1, global_ia_pn, global_ia_pm
global_ia_turbo, global_ia_vf
global_cfc_p0, global_cfc_p1, global_cfc_pn, global_cfc_pm
global_io_p0, global_io_p1, global_io_pn, global_io_pm
```

---

## NEW CLASSES IN DMR (Not in CoreManipulation)

### 1. **`BootConfiguration` Class** ⭐ NEW
**Location**: Lines 382-494 in DMR

**Purpose**: Structured configuration management for boot operations

**Key Features:**
- Type hints with Optional[int], Optional[bool], etc.
- Separate frequency configs for IA, IMH, CFC (FW, CBB, IO, MEM)
- Methods:
  - `apply_global_overrides(global_config: Dict)`
  - `apply_fixed_frequencies()`
  - `print_configuration()`

**Recommendation**: **MIGRATE** - This is a significant improvement over scattered global variables

---

### 2. **`SystemBooter` Class** ⭐ NEW
**Location**: Lines 497-1067 in DMR

**Purpose**: Clean separation of boot logic from System2Tester class

**Key Features:**
- Handles both bootscript and fastboot methods
- Fuse management and verification
- Boot retry logic
- Methods:
  - `boot(use_fastboot, **boot_params)`
  - `_execute_bootscript()`
  - `_execute_fastboot()`
  - `_build_fuse_strings()`
  - `_apply_frequency_fuses()`
  - `_apply_license_mode()`
  - `_apply_ppvc_fuses()`
  - `_build_mask_strings()`
  - `_build_bootscript_fuse_string()`
  - `_build_fuse_files_string()`
  - `_assign_values_to_regs()`
  - `_retry_boot()`
  - `_check_boot_completion()`
  - `verify_fuses()`

**Recommendation**: **MIGRATE** - Major architectural improvement for maintainability

---

## UPDATED `System2Tester` CLASS

### DMR Enhancements

#### New Instance Variables:
```python
self.cbbs = sv.socket0.cbbs  # Instead of computes
self.imhs = sv.socket0.imhs  # Instead of ios
self.dis_1CPM = dis_1CPM  # New parameter
self.fuse_1CPM = ...  # New fuse array
self.debug = False  # Debug mode flag
self.booter = SystemBooter(...)  # NEW: Boot operations delegated
```

#### New Methods in DMR:
1. **`set_debug_mode()` / `disable_debug_mode()`** ⭐ NEW
   - Enable/disable debug mode during execution

2. **`_init_system_booter()`** ⭐ NEW
   - Initialize SystemBooter with configuration

3. **`_apply_global_boot_config()`** ⭐ NEW
   - Apply global boot settings to booter

4. **`check_for_start_fresh()`** ⭐ NEW
   - Check and reset globals if needed

5. **`check_product_validity()`** ⭐ NEW
   - Validate product support

6. **`generate_base_dict()`** ⭐ NEW
   - Generate CBB base dictionary

7. **`generate_module_mask()`** ⭐ NEW
   - Generate module masking info

8. **`generate_mesh_masking()`** ⭐ NEW
   - Generate mesh masking from masks dict

9. **`generate_first_enabled_mask()`** ⭐ NEW
   - Find first enabled module for WA

10. **`convert_cbb_mask_to_compute_mask()`** ⭐ NEW
    - Convert CBB-level masks to compute-level

11. **`convert_compute_mask_to_cbb_mask()`** ⭐ NEW
    - Convert compute-level masks to CBB-level

12. **`get_compute_config()`** ⭐ NEW
    - Get CBB list and config string

13. **`assign_values_to_regs()`** ⭐ NEW
    - Assign values to register list

#### Modified Methods in DMR:
1. **`setModule()`** (was `setCore()` in GNR)
   - Renamed for DMR terminology
   - Uses CBB instead of compute terminology
   - More modular structure with helper methods

2. **`setCompute()`** (NEW in DMR, no equivalent in GNR)
   - Enables/disables specific computes within CBBs

3. **`setTile()`**
   - Updated to use CBB terminology
   - More structured with helper methods

4. **`setmesh()`**
   - Enhanced parameter support (dis_1CPM added)

5. **`setfc()`**
   - Similar structure, cleaner implementation

6. **`_call_boot()`** (was `_doboot()` / `_fastboot()` in GNR)
   - Unified boot method using SystemBooter
   - Cleaner parameter handling
   - All frequency parameters explicitly passed

#### Removed Methods from GNR:
- `_doboot()` - Merged into SystemBooter
- `_fastboot()` - Merged into SystemBooter
- `fuse_checks()` - Integrated into SystemBooter.verify_fuses()
- `bsRetry()` - Moved to SystemBooter._retry_boot()
- `bsCheck()` - Moved to SystemBooter._check_boot_completion()

---

## STANDALONE FUNCTIONS COMPARISON

### Functions in DMR but NOT in CoreManipulation:

1. **`get_compute_config()`** ⭐ NEW (Line ~1667)
   - Returns CBB list and configuration string
   - **Action**: MIGRATE

2. **`assign_values_to_regs()`** ⭐ NEW (Line ~1674)
   - Helper to assign values to register lists
   - **Action**: MIGRATE

### Functions with SIGNIFICANT UPDATES in DMR:

1. **`mask_fuse_module_array()`** (was `mask_fuse_core_array()`)
   - **Changes**:
     - Uses CBB terminology instead of compute
     - Different register paths: `sv.socket0.{cbb_name}.base.fuses.punit_fuses.fw_fuses_sst_pp_*`
     - Removed capid_capid8/9 llc_ia_core_en registers
   - **Action**: REVIEW & ADAPT for DMR

2. **`mask_fuse_llc_array()`**
   - **Changes**:
     - Uses CBB terminology
     - Different register: `sv.socket0.{cbb_name}.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis`
     - Removed capid_capid6/7 llc_slice_en registers
   - **Action**: REVIEW & ADAPT for DMR

3. **`fuse_cmd_override_reset()`**
   - **Changes**:
     - Uses `sv.sockets.cbbs.base.fuses` instead of `sv.sockets.computes.fuses`
     - Uses `sv.sockets.imhs.fuses` instead of `sv.sockets.ios.fuses`
     - Different postcode register: `sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]`
   - **Action**: UPDATE for DMR architecture

4. **`fuse_cmd_override_check()`**
   - **Changes**:
     - Updated bsf dictionary with CBB/IMH keys
     - `'cbb0'`, `'cbb1'`, `'cbb2'`, `'cbb3'`, `'imh0'`, `'imh1'`
   - **Action**: UPDATE dictionary keys

5. **`CheckModule()`** (was `CheckCore()`)
   - **Changes**:
     - Uses `TOTAL_MODULES_PER_CBB` instead of `MAXPHYSICAL`
     - Checks `ia_cbb{target_cbb}` instead of `ia_compute_{target_comp}`
   - **Action**: RENAME & UPDATE

6. **`CheckMasks()`**
   - **Changes**:
     - Uses `sv.socket0.cbbs` iteration
     - Keys: `ia_{cbb_name}`, `llc_{cbb_name}`
     - Uses `TOTAL_MODULES_PER_CBB` for offset calculation
   - **Action**: UPDATE for CBB iteration

7. **`modulesEnabled()`** (was `coresEnabled()`)
   - **Changes**:
     - Uses CBB terminology throughout
     - Updated column/row structure for DMR tileview
     - Different physical module layout
   - **Action**: SIGNIFICANT REFACTOR needed

8. **`read_postcode()`**
   - **Changes**:
     - Uses `sv.socket0.imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]`
     - Instead of `sv.socket0.io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg`
   - **Action**: UPDATE register path

9. **`clear_biosbreak()`**
   - **Changes**:
     - Uses `sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]`
     - Instead of `sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg`
   - **Action**: UPDATE register path

10. **`_logical_to_physical()` / `_physical_to_logical()`**
    - **Changes**:
      - Uses `cbb_instance` parameter instead of `compute_instance` or `cinst`
      - Uses `TOTAL_ACTIVE_MODULES_PER_CBB` and `TOTAL_MODULES_PER_CBB`
    - **Action**: UPDATE parameter names and constants

11. **`_module_mask_phy_to_log()` / `_module_mask_log_to_phy()`**
    - **Changes**:
      - Uses `TOTAL_MODULES_PER_CBB` and `TOTAL_ACTIVE_MODULES_PER_CBB`
      - Uses `skip_physical_modules` instead of `skip_cores_10x5`
    - **Action**: UPDATE constants and variable names

12. **`_module_string()`** (was `_core_string()`)
    - **Changes**:
      - Uses `TOTAL_MODULES_PER_CBB` and `cbbinst` parameter
      - Uses `skip_physical_modules`
    - **Action**: RENAME & UPDATE

13. **`_module_apic_id()`** (was `_core_apic_id()`)
    - **Changes**:
      - Uses `TOTAL_MODULES_PER_CBB` and `TOTAL_MODULES_PER_COMPUTE`
      - Calculates `cbb_index` and `compute_index` differently
      - Uses postcode register `sv.socket0.imh0.ubox.ncdecs.biosscratchpad_mem[6]`
    - **Action**: UPDATE for DMR architecture

14. **`_enabled_bit_array()`** (NEW name, was `_bit_array()`)
    - **Changes**:
      - Different default: `max_bit = TOTAL_MODULES_PER_CBB`
      - Returns enabled (0) bits instead of disabled (1) bits
    - **Action**: REVIEW logic difference

### Functions IDENTICAL or MINOR CHANGES:

1. **`gen_product_bootstring()`**
   - Minor changes in parameter structure
   - **Action**: UPDATE for DMR bootscript format

2. **`svStatus()`**
   - Nearly identical
   - **Action**: NO CHANGE NEEDED

3. **`check_user_cancel()`**
   - Identical
   - **Action**: NO CHANGE NEEDED

4. **`go_to_efi()`**
   - Updated postcode register
   - **Action**: UPDATE register paths

5. **`_wait_for_post()`**
   - Uses `read_postcode()` (which is updated)
   - **Action**: UPDATE via read_postcode()

6. **Bit manipulation functions**:
   - `_bitsoncount()`, `_bitsoffcount()`, `_bit_check()`, `_set_bit()`, `_set_bits()`, `_enable_bits()`
   - **Action**: NO CHANGE NEEDED (identical)

### Functions in GNR but NOT in DMR:

1. **`_phy2log()`** / **`_log2phy()`**
   - Complex physical to logical mapping using core matrix
   - **Action**: EVALUATE if needed for DMR

2. **`_core_dis_phy_to_log()` / `_core_dis_log_to_phy()`**
   - Uses `skip_cores_10x5` and `MAXLOGICAL`/`MAXPHYSICAL`
   - **Action**: REPLACED by `_module_mask_*` functions in DMR

### Debug Functions (GNR only):

- `fuse_cmd_override_reset_test()`
- `fuse_break()`, `fuse_break_nobs()`, `fuse_release()`, `fuse_release_nobs()`, `fuse_break_check_nobs()`
- **Action**: EVALUATE if needed for DMR debugging

---

## MIGRATION RECOMMENDATIONS

### HIGH PRIORITY (Must Migrate):

1. ✅ **Migrate `BootConfiguration` class**
   - Provides structured boot parameter management
   - Eliminates scattered global variables
   - Adds type safety with type hints

2. ✅ **Migrate `SystemBooter` class**
   - Clean separation of concerns
   - Easier testing and maintenance
   - Unified boot/fastboot logic

3. ✅ **Update `System2Tester.__init__()`**
   - Add `self.cbbs`, `self.imhs`
   - Add `dis_1CPM` support
   - Add `self.booter` initialization
   - Add debug mode support

4. ✅ **Update `System2Tester` methods**:
   - Rename `setCore()` → `setModule()`
   - Add `setCompute()` method
   - Update `setTile()` for CBB terminology
   - Replace `_doboot()`/`_fastboot()` with `_call_boot()`
   - Add helper methods (check_*, generate_*, convert_*)

### MEDIUM PRIORITY (Should Update):

5. ✅ **Update fuse mask functions**:
   - `mask_fuse_module_array()` (from `mask_fuse_core_array()`)
   - `mask_fuse_llc_array()`
   - Update register paths for DMR

6. ✅ **Update fuse override functions**:
   - `fuse_cmd_override_reset()`
   - `fuse_cmd_override_check()`
   - Update for CBB/IMH terminology

7. ✅ **Update check functions**:
   - `CheckModule()` (from `CheckCore()`)
   - `CheckMasks()`

8. ✅ **Update utility functions**:
   - `modulesEnabled()` (from `coresEnabled()`)
   - `_module_string()` (from `_core_string()`)
   - `_module_apic_id()` (from `_core_apic_id()`)

### LOW PRIORITY (Nice to Have):

9. ⚠️ **Update postcode functions**:
   - `read_postcode()`, `clear_biosbreak()`
   - Change register paths

10. ⚠️ **Update conversion functions**:
    - `_logical_to_physical()`, `_physical_to_logical()`
    - `_module_mask_phy_to_log()`, `_module_mask_log_to_phy()`
    - Update parameter names and constants

11. ⚠️ **Evaluate GNR-specific functions**:
    - `_phy2log()`, `_log2phy()` - May not be needed for DMR
    - Debug fuse break functions - Keep if useful for DMR debugging

---

## CRITICAL DIFFERENCES TO HANDLE

### 1. **Terminology Translation Table**

| Function | GNR Term | DMR Term |
|----------|----------|----------|
| Die naming | `compute0`, `io0` | `cbb0`, `imh0` |
| Register base | `.fuses.` | `.base.fuses.` or `.fuses.` |
| PCU path | `.fuses.pcu.` | `.base.fuses.punit_fuses.` |
| Module count | `MAXPHYSICAL` (60) | `TOTAL_MODULES_PER_CBB` (32) |
| Logical count | `MAXLOGICAL` (44) | `TOTAL_ACTIVE_MODULES_PER_CBB` (24) |
| Skip list | `skip_cores_10x5` | `skip_physical_modules` |

### 2. **Register Path Changes**

| Register Type | GNR Path | DMR Path |
|---------------|----------|----------|
| Fuse disable | `compute.fuses.hwrs_top_rom.ip_disable_fuses_dword6_core_disable` | N/A (different structure) |
| PP masks | `compute.fuses.pcu.pcode_sst_pp_*_core_disable_mask` | `cbb.base.fuses.punit_fuses.fw_fuses_sst_pp_*_module_disable_mask` |
| LLC disable | `compute.fuses.hwrs_top_late.ip_disable_fuses_dword2_llc_disable` | `cbb.base.fuses.punit_fuses.fw_fuses_llc_slice_ia_ccp_dis` |
| Postcode read | `io0.uncore.ubox.ncdecs.biosnonstickyscratchpad7_cfg` | `imh0.ubox.ncdecs.biosnonstickyscratchpad_mem[7]` |
| Postcode break | `io0.uncore.ubox.ncdecs.biosscratchpad6_cfg` | `imh0.ubox.ncdecs.biosscratchpad_mem[6]` |

### 3. **Fuse Structure Differences**

**GNR has:**
- `sv.sockets.computes.fuses.load_fuse_ram()`
- `sv.sockets.ios.fuses.load_fuse_ram()`

**DMR uses:**
- `sv.sockets.cbbs.base.fuses.load_fuse_ram()`
- `sv.sockets.imhs.fuses.load_fuse_ram()`

### 4. **Bootscript Format Differences**

**GNR:**
```python
b.go(fused_unit=True, compute_config="GNRUCC", segment="X3", 
     ia_core_disable={'compute0': 0x...}, llc_slice_disable={'compute0': 0x...},
     fuse_str_compute_0=[...], fuse_str_io_0=[...])
```

**DMR:**
```python
b.go(fused_unit=False, pwrgoodmethod="usb", compute_config="X1",
     ia_core_disable={'cbb_base0': 0x...}, llc_slice_disable={'cbb_base0': 0x...},
     fuse_str={'cbb_base': [...], 'imh': [...]})
```

---

## FUNCTION-BY-FUNCTION DECISION MATRIX

| Function Name | Exists in CoreManip? | Updated in DMR? | Action | Priority |
|---------------|---------------------|-----------------|--------|----------|
| `BootConfiguration` class | ❌ No | ✅ NEW | **MIGRATE** | HIGH |
| `SystemBooter` class | ❌ No | ✅ NEW | **MIGRATE** | HIGH |
| `reset_globals()` | ✅ Yes | ✅ Enhanced | **UPDATE** | HIGH |
| `System2Tester.__init__()` | ✅ Yes | ✅ Enhanced | **UPDATE** | HIGH |
| `System2Tester.setModule()` | ❌ No (setCore) | ✅ Renamed | **MIGRATE** | HIGH |
| `System2Tester.setCompute()` | ❌ No | ✅ NEW | **MIGRATE** | HIGH |
| `System2Tester.setTile()` | ✅ Yes | ✅ Updated | **UPDATE** | HIGH |
| `System2Tester.setmesh()` | ✅ Yes | ✅ Updated | **UPDATE** | MEDIUM |
| `System2Tester.setfc()` | ✅ Yes | ✅ Updated | **UPDATE** | MEDIUM |
| `System2Tester._call_boot()` | ❌ No | ✅ NEW | **MIGRATE** | HIGH |
| `System2Tester._doboot()` | ✅ Yes | ❌ Removed | **REMOVE** (use SystemBooter) | HIGH |
| `System2Tester._fastboot()` | ✅ Yes | ❌ Removed | **REMOVE** (use SystemBooter) | HIGH |
| `System2Tester.fuse_checks()` | ✅ Yes | ❌ Removed | **REMOVE** (use SystemBooter.verify_fuses) | MEDIUM |
| `System2Tester.bsRetry()` | ✅ Yes | ❌ Removed | **REMOVE** (use SystemBooter._retry_boot) | MEDIUM |
| `System2Tester.bsCheck()` | ✅ Yes | ❌ Removed | **REMOVE** (use SystemBooter._check_boot_completion) | MEDIUM |
| `gen_product_bootstring()` | ✅ Yes | ✅ Updated | **UPDATE** | HIGH |
| `mask_fuse_module_array()` | ✅ Yes (core_array) | ✅ Renamed/Updated | **UPDATE** | HIGH |
| `mask_fuse_llc_array()` | ✅ Yes | ✅ Updated | **UPDATE** | HIGH |
| `fuse_cmd_override_reset()` | ✅ Yes | ✅ Updated | **UPDATE** | HIGH |
| `fuse_cmd_override_check()` | ✅ Yes | ✅ Updated | **UPDATE** | MEDIUM |
| `CheckModule()` | ✅ Yes (CheckCore) | ✅ Renamed/Updated | **UPDATE** | MEDIUM |
| `CheckMasks()` | ✅ Yes | ✅ Updated | **UPDATE** | MEDIUM |
| `modulesEnabled()` | ✅ Yes (coresEnabled) | ✅ Renamed/Updated | **UPDATE** | MEDIUM |
| `read_postcode()` | ✅ Yes (read_biospost) | ✅ Updated | **UPDATE** | MEDIUM |
| `clear_biosbreak()` | ✅ Yes | ✅ Updated | **UPDATE** | MEDIUM |
| `go_to_efi()` | ✅ Yes | ✅ Updated | **UPDATE** | MEDIUM |
| `_wait_for_post()` | ✅ Yes | ✅ Updated | **UPDATE** | MEDIUM |
| `_logical_to_physical()` | ✅ Yes | ✅ Updated | **UPDATE** | LOW |
| `_physical_to_logical()` | ✅ Yes | ✅ Updated | **UPDATE** | LOW |
| `_module_mask_phy_to_log()` | ✅ Yes (_core_dis_phy_to_log) | ✅ Renamed/Updated | **UPDATE** | LOW |
| `_module_mask_log_to_phy()` | ✅ Yes (_core_dis_log_to_phy) | ✅ Renamed/Updated | **UPDATE** | LOW |
| `_module_string()` | ✅ Yes (_core_string) | ✅ Renamed/Updated | **UPDATE** | LOW |
| `_module_apic_id()` | ✅ Yes (_core_apic_id) | ✅ Renamed/Updated | **UPDATE** | LOW |
| `_enabled_bit_array()` | ✅ Yes (_bit_array) | ✅ Logic Changed | **UPDATE** | LOW |
| `_phy2log()` / `_log2phy()` | ✅ Yes | ❌ Not in DMR | **EVALUATE** if needed | LOW |
| `_core_dr_registers()` | ✅ Yes | ✅ Similar | **NO CHANGE** | LOW |
| Bit manipulation functions | ✅ Yes | ✅ Identical | **NO CHANGE** | LOW |
| Debug fuse functions | ✅ Yes | ❌ Not in DMR | **EVALUATE** if needed | LOW |

---

## STEP-BY-STEP MIGRATION PLAN

### Phase 1: Core Architecture (Week 1)
1. Add `typing` imports to CoreManipulation.py
2. Migrate `BootConfiguration` class
3. Migrate `SystemBooter` class
4. Update global variable declarations (add DMR-specific ones)
5. Update `reset_globals()` to include all DMR variables

### Phase 2: System2Tester Class Updates (Week 2)
6. Update `System2Tester.__init__()`:
   - Add `cbbs`, `imhs`, `dis_1CPM` support
   - Initialize `self.booter`
   - Add debug mode support
7. Add helper methods: `_init_system_booter()`, `_apply_global_boot_config()`
8. Add validation methods: `check_for_start_fresh()`, `check_product_validity()`
9. Add generation methods: `generate_base_dict()`, `generate_module_mask()`, etc.

### Phase 3: Method Migration (Week 3)
10. Rename `setCore()` → `setModule()` and update logic
11. Add new `setCompute()` method
12. Update `setTile()` for CBB terminology
13. Update `setmesh()` with `dis_1CPM` parameter
14. Update `setfc()`
15. Replace `_doboot()` and `_fastboot()` with unified `_call_boot()`

### Phase 4: Standalone Function Updates (Week 4)
16. Update `gen_product_bootstring()` for DMR format
17. Update `mask_fuse_module_array()` (from `mask_fuse_core_array()`)
18. Update `mask_fuse_llc_array()`
19. Update `fuse_cmd_override_reset()` and `fuse_cmd_override_check()`
20. Update `CheckModule()` (from `CheckCore()`)
21. Update `CheckMasks()`

### Phase 5: Utility Functions (Week 5)
22. Update `modulesEnabled()` (from `coresEnabled()`)
23. Update postcode functions: `read_postcode()`, `clear_biosbreak()`
24. Update `go_to_efi()` and `_wait_for_post()`
25. Update `_module_string()`, `_module_apic_id()`
26. Update conversion functions: `_logical_to_physical()`, etc.

### Phase 6: Testing & Validation (Week 6)
27. Create test cases for each migrated function
28. Validate boot operations (bootscript and fastboot)
29. Validate fuse operations
30. Validate masking operations
31. Performance testing and optimization

---

## TESTING CHECKLIST

### Unit Tests Needed:
- [ ] `BootConfiguration` initialization and methods
- [ ] `SystemBooter` boot operations
- [ ] `System2Tester.setModule()`
- [ ] `System2Tester.setCompute()`
- [ ] `System2Tester.setTile()`
- [ ] `System2Tester.setmesh()`
- [ ] Fuse mask generation functions
- [ ] Fuse override operations
- [ ] Mask checking functions
- [ ] Postcode operations
- [ ] Conversion functions

### Integration Tests Needed:
- [ ] Full boot cycle with bootscript
- [ ] Full boot cycle with fastboot
- [ ] Multi-CBB configurations
- [ ] Various masking configurations
- [ ] Frequency override scenarios
- [ ] License mode configurations
- [ ] PPVC fuse application

### Regression Tests:
- [ ] Existing GNR functionality still works
- [ ] DMR-specific functionality works
- [ ] No breaking changes to public API

---

## RISK ASSESSMENT

### HIGH RISK Areas:
1. **Boot Logic Changes**: SystemBooter refactoring - Test thoroughly
2. **Register Path Changes**: DMR uses different paths - Validate all register accesses
3. **Terminology Changes**: CBB/IMH vs Compute/IO - Ensure consistency

### MEDIUM RISK Areas:
1. **Fuse Handling**: Different fuse structures between GNR and DMR
2. **Mask Conversions**: Physical/logical conversions differ
3. **Tileview Display**: Module layout different in DMR

### LOW RISK Areas:
1. **Bit Manipulation**: Functions identical
2. **User Cancel**: Logic unchanged
3. **Utility Functions**: Minor changes only

---

## CONCLUSION

**Key Findings:**
1. DMR introduces **2 major new classes** (`BootConfiguration`, `SystemBooter`) that significantly improve code organization
2. **~40% of functions** need updates for DMR terminology and architecture
3. **Core logic** remains similar, but **register paths and naming** differ significantly
4. **New methods** in `System2Tester` provide better modularity

**Recommendation:**
1. **MIGRATE** the new classes (HIGH PRIORITY) - They represent architectural improvements
2. **UPDATE** existing functions systematically following the phase plan
3. **MAINTAIN** backward compatibility where possible for GNR
4. **TEST** thoroughly at each phase before moving to the next

**Estimated Effort:**
- Migration: ~6 weeks with proper testing
- Risk Level: Medium (mostly terminology and path changes)
- Benefit: High (improved maintainability, cleaner architecture)

