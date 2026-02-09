# MaskEditor DMR Migration Guide

## Overview
The MaskEditor has been updated to support DMR's CBB-based (Compute Building Block) configuration instead of the previous compute-based configuration.

## Key Changes

### 1. Architecture Change
- **Old**: Compute-based (compute0, compute1, compute2) with 60-bit masks per compute
- **New**: CBB-based (cbb0, cbb1, cbb2, cbb3) with 32-bit masks per CBB

### 2. Mask Format

#### Old Format (Compute-based - GNR/CWF)
```python
compute0_core_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"  # 64 hex chars
compute0_cha_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"   # 64 hex chars
compute1_core_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"
compute1_cha_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"
compute2_core_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"
compute2_cha_hex = "0x0000000000000000000000000000000000000000000000000000000000000000"
```

#### New Format (CBB-based - DMR)
```python
cbb0_core_hex = "0x00000000"  # 8 hex chars (32 bits)
cbb0_llc_hex = "0x00000000"   # 8 hex chars (32 bits)
cbb1_core_hex = "0x00000000"
cbb1_llc_hex = "0x00000000"
cbb2_core_hex = "0x00000000"
cbb2_llc_hex = "0x00000000"
cbb3_core_hex = "0x00000000"
cbb3_llc_hex = "0x00000000"
```

### 3. Dictionary Keys

#### Old Keys
- `"ia_compute_0"`, `"ia_compute_1"`, `"ia_compute_2"`
- `"llc_compute_0"`, `"llc_compute_1"`, `"llc_compute_2"`

#### New Keys
- `"ia_cbb0"`, `"ia_cbb1"`, `"ia_cbb2"`, `"ia_cbb3"`
- `"llc_cbb0"`, `"llc_cbb1"`, `"llc_cbb2"`, `"llc_cbb3"`

### 4. UI Grid Layout

#### Old Layout (Compute-based)
- 7 rows × 10 columns = 70 positions
- 60 active module/CHA positions
- Special positions for MC and SPK components

#### New Layout (DMR CBB-based)
- 8 rows × 4 columns = 32 positions
- All 32 positions are active module/LLC positions
- Simplified grid matching DMR tile architecture

The layout follows the DMR tileview from CoreManipulation.py:
```
       DCM0  DCM1  DCM2  DCM3
ROW0:   0     1     2     3
ROW1:   4     5     6     7
ROW2:   8     9    10    11
ROW3:  12    13    14    15
ROW4:  16    17    18    19
ROW5:  20    21    22    23
ROW6:  24    25    26    27
ROW7:  28    29    30    31
```

## Usage Examples

### Basic Usage
```python
import tkinter as tk
from MaskEditor import SystemMaskEditor

# Initialize with CBB masks
editor = SystemMaskEditor(
    cbb0_core_hex="0x00000000",
    cbb0_llc_hex="0x00000000",
    cbb1_core_hex="0x00000000",
    cbb1_llc_hex="0x00000000",
    cbb2_core_hex="0x00000000",
    cbb2_llc_hex="0x00000000",
    cbb3_core_hex="0x00000000",
    cbb3_llc_hex="0x00000000",
    product='DMR'
)

root = tk.Tk()
masks = editor.start(root)

# Access results
print("CBB0 Module mask:", masks["ia_cbb0"])
print("CBB0 LLC mask:", masks["llc_cbb0"])
```

### Using the Masking Helper Function
```python
import tkinter as tk
from MaskEditor import Masking

def my_callback(masks):
    print("Masks updated:", masks)

root = tk.Tk()
masks = Masking(
    root,
    cbb0_core_hex="0x00000000",
    cbb0_llc_hex="0x00000000",
    cbb1_core_hex="0x00000000",
    cbb1_llc_hex="0x00000000",
    cbb2_core_hex="0x00000000",
    cbb2_llc_hex="0x00000000",
    cbb3_core_hex="0x00000000",
    cbb3_llc_hex="0x00000000",
    product='DMR',
    callback=my_callback
)
```

### Single CBB Configuration
```python
# Only configure CBB0 (others optional)
editor = SystemMaskEditor(
    cbb0_core_hex="0x00000001",  # Disable module 0
    cbb0_llc_hex="0x00000003",   # Disable LLCs 0 and 1
    product='DMR'
)
```

### Integration with CoreManipulation
```python
# Example: Using masks from MaskEditor in CoreManipulation
from MaskEditor import Masking
import CoreManipulation as cm

# Get masks from UI
root = tk.Tk()
masks = Masking(root, "0x0", "0x0", "0x0", "0x0", "0x0", "0x0", "0x0", "0x0", product='DMR')

# Use with CoreManipulation functions
cm.modulesEnabled(
    moduleslicemask={
        'ia_cbb0': int(masks['ia_cbb0'], 16),
        'ia_cbb1': int(masks['ia_cbb1'], 16),
        'ia_cbb2': int(masks['ia_cbb2'], 16),
        'ia_cbb3': int(masks['ia_cbb3'], 16),
        'llc_cbb0': int(masks['llc_cbb0'], 16),
        'llc_cbb1': int(masks['llc_cbb1'], 16),
        'llc_cbb2': int(masks['llc_cbb2'], 16),
        'llc_cbb3': int(masks['llc_cbb3'], 16),
    },
    logical=False,
    print_modules=True,
    print_llcs=True
)
```

## Migration Checklist

If you have existing code using the old MaskEditor:

1. **Update function signatures**:
   - Change from `compute0/1/2_core/cha_hex` to `cbb0/1/2/3_core/llc_hex`

2. **Update hex string lengths**:
   - Change from 64-character hex strings to 8-character hex strings

3. **Update dictionary keys**:
   - Change from `"ia_compute_N"` to `"ia_cbbN"`
   - Change from `"llc_compute_N"` to `"llc_cbbN"`

4. **Add CBB3 support**:
   - DMR supports 4 CBBs (0-3) instead of 3 computes (0-2)

5. **Update product names**:
   - Use `product='DMR'` instead of `product='GNR'` or `product='CWF'`

## Technical Details

### Bit Ordering
- Bits are stored in reverse order (LSB first) for UI display
- Module indexing follows column-first order: DCM0 (0-7), DCM1 (8-15), DCM2 (16-23), DCM3 (24-31)

### Module Naming
- DMR uses "MODULE" terminology instead of "CORE"
- LLCs are still called "LLC" (not CHA)

### Button States
- Green: Module/LLC enabled (bit = 0)
- Red: Module/LLC disabled (bit = 1)
- Click to toggle state

## Compatibility

The updated MaskEditor:
- ✅ Supports DMR CBB-based configuration (primary)
- ✅ Maintains backward compatibility structure for future products
- ✅ Follows DMR tileview architecture from CoreManipulation.py
- ✅ Uses 32-bit masks per CBB (MODS_PER_CBB = 32)
- ✅ Supports up to 4 CBBs (configurable)

## Testing

Run the built-in test function:
```python
import tkinter as tk
from MaskEditor import test_UI

root = tk.Tk()
test_UI(root)
```

This will launch the MaskEditor UI with all CBBs initialized to 0x00000000 (all modules/LLCs enabled).
