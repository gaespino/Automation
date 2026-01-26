# External Fuse Files (.fuse) - Quick Reference Guide

**Version:** 1.0
**Release Date:** January 21, 2026
**Products:** DMR, GNR, CWF
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

---

## Overview

External `.fuse` files allow you to define custom register configurations in a simple, human-readable format. The framework automatically parses these files and integrates them into bootscripts.

## Quick Start

### 1. Create a Fuse File

**DMR Example** (`my_dmr_fuses.fuse`):
```ini
# Specific CBB fuses
[sv.socket0.cbb0.base.fuses]
register1 = 0x1
register2 = 0xFF

# Applied to all CBBs
[sv.socket0.cbbs.base.fuses]
common_register = 0x1234
```

**GNR/CWF Example** (`my_gnr_fuses.fuse`):
```ini
# Specific compute fuses
[sv.socket0.compute0.fuses]
register1 = 0x1
register2 = 0xFF

# Applied to all computes
[sv.socket0.computes.fuses]
common_register = 0x1234
```

### 2. Use in Code

```python
import S2T.dpmChecks as dpm

# Parse the file
fuses = dpm.process_fuse_file('C:\\Temp\\my_fuses.fuse')

# Process for bootscript
config = dpm.external_fuses(external_fuses=fuses, bsformat=True)

# Use in pseudo_bs
dpm.pseudo_bs(
    ClassMask='RowEvenPass',
    fuse_cbb=config,
    boot=True
)
```

### 3. Use in UI

```python
import S2T.UI.System2TesterUI as ui
import S2T.SetTesterRegs as s2t

# Launch UI
ui.mesh_ui(s2t, 'DMR')

# Click "Browse" next to "External Fuse File (.fuse):"
# Select your .fuse file and run
```

---

## File Format

### Basic Syntax

```ini
# Comments start with #
[section.header]
key = value
fully.qualified.key = value
```

### Rules

1. **Sections:** Must match product hierarchy
2. **Keys:** Register names (can be partial or fully qualified)
3. **Values:** Hex values without quotes (`0xFF` not `"0xFF"`)
4. **Comments:** Lines starting with `#`
5. **Whitespace:** Ignored around `=`

---

## Section Hierarchies

### DMR Sections

| Pattern | Example | Description |
|---------|---------|-------------|
| `socket(s\|#).cbb(s\|#).base.fuses` | `socket0.cbb0.base.fuses` | CBB base fuses |
| `socket(s\|#).cbb(s\|#).compute(s\|#).fuses` | `socket0.cbb0.compute0.fuses` | CBB compute fuses |
| `socket(s\|#).imh(s\|#).fuses` | `socket0.imh0.fuses` | IMH fuses |

### GNR/CWF Sections

| Pattern | Example | Description |
|---------|---------|-------------|
| `socket(s\|#).compute(s\|#).fuses` | `socket0.compute0.fuses` | Compute fuses |
| `socket(s\|#).io(s\|#).fuses` | `socket0.io0.fuses` | IO fuses |

### Naming Flexibility

**All these are valid:**

```ini
# Specific units
[sv.socket0.cbb0.base.fuses]

# All of a type (plural)
[sv.socket0.cbbs.base.fuses]

# Mix specific and plural
[sv.socket0.cbbs.compute0.fuses]
[sv.sockets.cbb0.base.fuses]
```

---

## Key Features

### 1. Native Hex Support

✅ **Correct:**
```ini
register = 0xFF
register = 0xDEADBEEF
```

❌ **Wrong:**
```ini
register = "0xFF"      # Don't use quotes
register = 255         # Use hex, not decimal
```

### 2. Automatic Expansion

**Input:**
```ini
[sv.socket0.cbbs.base.fuses]
common_reg = 0xFF
```

**Output** (system with cbb0-cbb3):
```python
[
    'sv.socket0.cbb0.base.fuses.common_reg=0xFF',
    'sv.socket0.cbb1.base.fuses.common_reg=0xFF',
    'sv.socket0.cbb2.base.fuses.common_reg=0xFF',
    'sv.socket0.cbb3.base.fuses.common_reg=0xFF'
]
```

### 3. System Validation

If you specify fuses for hardware that doesn't exist:

```
WARNING: Fuses for cbb2 are included but system does not have cbb2.
Fuses will NOT be applied.
```

### 4. Partial vs Full Paths

**Partial path:**
```ini
[sv.socket0.cbb0.base.fuses]
register1 = 0x1
```
→ `sv.socket0.cbb0.base.fuses.register1=0x1`

**Full path:**
```ini
[sv.socket0.cbb0.base.fuses]
sv.socket0.cbb0.base.fuses.register1 = 0x1
```
→ `sv.socket0.cbb0.base.fuses.register1=0x1`

Both produce the same output.

---

## Complete Examples

### DMR Complete Example

**File:** `dmr_config.fuse`

```ini
# CBB0 Base fuses
[sv.socket0.cbb0.base.fuses]
base_register1 = 0x1
base_register2 = 0x2

# CBB0 Compute0 fuses
[sv.socket0.cbb0.compute0.fuses]
compute_register1 = 0x1
compute_register2 = 0xFF

# IMH0 fuses
[sv.socket0.imh0.fuses]
imh_register1 = 0xDEAD
imh_register2 = 0xBEEF

# Common fuses for all CBBs
[sv.socket0.cbbs.base.fuses]
common_base_reg = 0x1234

# Common fuses for all CBB computes
[sv.socket0.cbbs.computes.fuses]
common_compute_reg = 0x5678

# Common fuses for all IMHs
[sv.socket0.imhs.fuses]
common_imh_reg = 0xABCD
```

### GNR Complete Example

**File:** `gnr_config.fuse`

```ini
# Compute0 fuses
[sv.socket0.compute0.fuses]
compute_register1 = 0x1
compute_register2 = 0x2

# Compute1 fuses
[sv.socket0.compute1.fuses]
compute_register1 = 0x3
compute_register2 = 0x4

# IO0 fuses
[sv.socket0.io0.fuses]
io_register1 = 0xDEAD
io_register2 = 0xBEEF

# Common fuses for all computes
[sv.socket0.computes.fuses]
common_compute_reg = 0x1234

# Common fuses for all IOs
[sv.socket0.ios.fuses]
common_io_reg = 0x5678
```

---

## API Reference

### process_fuse_file()

**Purpose:** Parse a .fuse file and return register list

```python
import S2T.dpmChecks as dpm

fuse_list = dpm.process_fuse_file(fuse_file_path)
```

**Parameters:**
- `fuse_file_path` (str): Path to .fuse file

**Returns:**
- `List[str]`: Register assignments in format `'register.path=value'`

**Raises:**
- `FileNotFoundError`: File doesn't exist
- `ValueError`: Parse error or validation failure

**Example:**
```python
try:
    fuses = dpm.process_fuse_file('C:\\Temp\\my_fuses.fuse')
    print(f"Loaded {len(fuses)} fuses")
    for fuse in fuses:
        print(f"  {fuse}")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Parse error: {e}")
```

### external_fuses()

**Purpose:** Organize and validate fuses for bootscript

```python
external_config = dpm.external_fuses(
    external_fuses=None,  # List of fuse strings
    bsformat=False        # Format for bootscript
)
```

**Parameters:**
- `external_fuses` (List[str], optional): Fuse list from `process_fuse_file()`
- `bsformat` (bool): Apply bootscript formatting

**Returns:**
- `dict`: Organized fuses by unit: `{'cbb0': [...], 'cbb1': [...], ...}`

**Example:**
```python
# Load and process
fuses = dpm.process_fuse_file('my_fuses.fuse')
config = dpm.external_fuses(external_fuses=fuses, bsformat=True)

# Result structure
# config = {
#     'cbb0': [...],
#     'cbb1': [...],
#     'cbb2': [...],
#     'cbb3': [...],
#     'imh0': [...],
#     'imh1': [...],
#     'cbbs': [...],  # Original common list
#     'imhs': [...]   # Original common list
# }
```

### Integration with pseudo_bs()

```python
# Complete workflow
fuses = dpm.process_fuse_file('my_fuses.fuse')
config = dpm.external_fuses(external_fuses=fuses, bsformat=True)

dpm.pseudo_bs(
    ClassMask='RowEvenPass',
    Custom=[],
    boot=True,
    fuse_cbb=config,      # Apply external fuses
    htdis=False,
    fast=False
)
```

---

## Error Handling

### Common Errors

**1. Invalid Section Header**

```
ERROR: Invalid section 'sv.socket0.invalid.fuses'.
Must match DMR hierarchy: socket(s|#).cbb(s|#).base.fuses, ...
```

**Fix:** Check section matches product hierarchy

**2. File Not Found**

```
ERROR: Fuse file not found: C:\Temp\my_fuses.fuse
```

**Fix:** Check file path and extension

**3. Invalid Syntax**

```
ERROR: Line 15: Invalid syntax: register1 0x1
```

**Fix:** Use `=` between key and value

**4. Unit Not Present**

```
WARNING: Fuses for cbb2 are included but system does not have cbb2.
Fuses will NOT be applied.
```

**Note:** This is a warning - other fuses will still be applied

---

## Best Practices

### 1. File Organization

```ini
# Group by unit type
# ==================

# --- CBB Base Fuses ---
[sv.socket0.cbb0.base.fuses]
# ...

# --- CBB Compute Fuses ---
[sv.socket0.cbb0.compute0.fuses]
# ...

# --- Common Fuses ---
[sv.socket0.cbbs.base.fuses]
# ...
```

### 2. Use Comments

```ini
# Power management fuses
[sv.socket0.cbb0.base.fuses]
power_limit = 0x1234  # Set max TDP
```

### 3. Hex Formatting

```ini
# Consistent hex formatting
register1 = 0x1       # Single digit
register2 = 0xFF      # Two digits
register3 = 0x1234    # Four digits
register4 = 0xDEADBEEF  # Eight digits
```

### 4. Version Control

```ini
# File: my_config.fuse
# Version: 1.2
# Date: 2026-01-21
# Author: Your Name
# Description: Custom fuse configuration for...

[sv.socket0.cbb0.base.fuses]
# ...
```

---

## Example Files

Example `.fuse` files are provided in:

```
S2T/product_specific/dmr/example_dmr_fuses.fuse
S2T/product_specific/gnr/example_gnr_fuses.fuse
S2T/product_specific/cwf/example_cwf_fuses.fuse
```

View these for complete working examples.

---

## Troubleshooting

### Problem: Fuses not applied

**Check:**
1. File path is correct
2. Section headers match product hierarchy
3. No parse errors (check console output)
4. Units exist on the system

### Problem: Parse error

**Check:**
1. All sections have `[brackets]`
2. All assignments use `=`
3. No quotes around hex values
4. File saved as UTF-8 or ASCII

### Problem: Wrong values applied

**Check:**
1. Hex values are correct format (0x prefix)
2. Register names are correct
3. No duplicate register assignments

---

## Related Documentation

- **User Manual:** [THR_DEBUG_FRAMEWORK_USER_MANUAL.md](THR_DEBUG_FRAMEWORK_USER_MANUAL.md)
- **Detailed Docs:** `S2T/product_specific/FUSEFILEGEN_README.md`
- **Examples:** `S2T/product_specific/<product>/example_*_fuses.fuse`

---

## Quick Command Reference

```python
# Parse file
fuses = dpm.process_fuse_file('my_fuses.fuse')

# Organize fuses
config = dpm.external_fuses(external_fuses=fuses, bsformat=True)

# Use in bootscript
dpm.pseudo_bs(ClassMask='RowEvenPass', fuse_cbb=config, boot=True)

# Use in UI
import S2T.UI.System2TesterUI as ui
ui.mesh_ui(s2t, 'DMR')  # Browse for .fuse file
```

---

**© 2026 Intel Corporation. Intel Confidential.**
