# MaskEditor DMR Visual Comparison

## Architecture Comparison

### OLD: Compute-Based (GNR/CWF)
```
┌─────────────────────────────────────────────────┐
│         3 COMPUTES (compute0, 1, 2)             │
│  Each with 60-bit masks (64 hex characters)     │
└─────────────────────────────────────────────────┘

Compute0: 0x0000...0000 (64 hex chars = 256 bits)
Compute1: 0x0000...0000 (64 hex chars = 256 bits)
Compute2: 0x0000...0000 (64 hex chars = 256 bits)
```

### NEW: CBB-Based (DMR)
```
┌─────────────────────────────────────────────────┐
│          4 CBBs (cbb0, 1, 2, 3)                 │
│   Each with 32-bit masks (8 hex characters)     │
└─────────────────────────────────────────────────┘

CBB0: 0x00000000 (8 hex chars = 32 bits)
CBB1: 0x00000000 (8 hex chars = 32 bits)
CBB2: 0x00000000 (8 hex chars = 32 bits)
CBB3: 0x00000000 (8 hex chars = 32 bits)
```

## UI Layout Comparison

### OLD Layout (7x10 grid)
```
        COL0  COL1  COL2  COL3  COL4  COL5  COL6  COL7  COL8  COL9
ROW0:   [0]   [1]   [2]   [3]   [4]   [5]   [6]   [7]   [8]   [9]
ROW1:   [10]  [11]  [12]  [13]  [14]  [15]  [16]  [17]  [18]  [19]
ROW2:   [20]  [21]  [22]  [23]  [24]  [25]  [26]  [27]  [28]  [29]
ROW3:   [30]  [31]  [32]  [33]  [34]  [35]  [36]  [37]  [38]  [39]
ROW4:   MC2   [40]  [41]  [42]  [43]  [44]  [45]  [46]  [47]  MC0
ROW5:   MC3   [48]  [49]  [50]  [51]  [52]  [53]  [54]  [55]  MC1
ROW6:   SPK0  [56]  [57]  [58]  [59]  ---   ---   ---   ---   SPK1

60 active positions + special positions (MC, SPK)
```

### NEW Layout (8x4 grid) - DMR Tileview
```
        DCM0  DCM1  DCM2  DCM3
ROW0:   [0]   [1]   [2]   [3]
ROW1:   [4]   [5]   [6]   [7]
ROW2:   [8]   [9]   [10]  [11]
ROW3:   [12]  [13]  [14]  [15]
ROW4:   [16]  [17]  [18]  [19]
ROW5:   [20]  [21]  [22]  [23]
ROW6:   [24]  [25]  [26]  [27]
ROW7:   [28]  [29]  [30]  [31]

32 active positions (all modules/LLCs)
Column-first ordering: DCM0=0-7, DCM1=8-15, DCM2=16-23, DCM3=24-31
```

## Code Changes Summary

### Before (Compute-based)
```python
class SystemMaskEditor:
    def __init__(self,
                 compute0_core_hex, compute0_cha_hex,
                 compute1_core_hex, compute1_cha_hex,
                 compute2_core_hex, compute2_cha_hex,
                 product='GNR', callback=None):

        self.masks = {
            "ia_compute_0": compute0_core_hex,
            "ia_compute_1": compute1_core_hex,
            "ia_compute_2": compute2_core_hex,
            "llc_compute_0": compute0_cha_hex,
            "llc_compute_1": compute1_cha_hex,
            "llc_compute_2": compute2_cha_hex
        }
```

### After (CBB-based)
```python
class SystemMaskEditor:
    def __init__(self,
                 cbb0_core_hex, cbb0_llc_hex,
                 cbb1_core_hex=None, cbb1_llc_hex=None,
                 cbb2_core_hex=None, cbb2_llc_hex=None,
                 cbb3_core_hex=None, cbb3_llc_hex=None,
                 product='DMR', callback=None):

        self.masks = {
            "ia_cbb0": cbb0_core_hex,
            "ia_cbb1": cbb1_core_hex,
            "ia_cbb2": cbb2_core_hex,
            "ia_cbb3": cbb3_core_hex,
            "llc_cbb0": cbb0_llc_hex,
            "llc_cbb1": cbb1_llc_hex,
            "llc_cbb2": cbb2_llc_hex,
            "llc_cbb3": cbb3_llc_hex
        }
```

## Key Features

### DMR-Specific Features
✅ **32-bit masks per CBB** (matches MODS_PER_CBB = 32)
✅ **4 CBB support** (cbb0-3)
✅ **8x4 tile layout** (matches DMR architecture)
✅ **Column-first indexing** (DCM0=0-7, DCM1=8-15, etc.)
✅ **Module/LLC terminology** (not Core/CHA)
✅ **Simplified grid** (no special MC/SPK positions)

### Backward Compatibility Maintained
✅ Product parameter for future flexibility
✅ Optional CBB parameters (only cbb0 required)
✅ Callback support for integration
✅ Same UI interaction model

## Bit Indexing Example

### DMR CBB0 Module Mask: 0x0000000F
```
Hex:  0x0000000F
Binary: 00000000 00000000 00000000 00001111
Bits:   31...........................3210

Disabled modules: 0, 1, 2, 3 (bits set to 1)
Enabled modules: 4-31 (bits set to 0)

Tile view:
        DCM0  DCM1  DCM2  DCM3
ROW0:   [X]   [✓]   [✓]   [✓]    X = disabled
ROW1:   [X]   [✓]   [✓]   [✓]    ✓ = enabled
ROW2:   [X]   [✓]   [✓]   [✓]
ROW3:   [X]   [✓]   [✓]   [✓]
ROW4:   [✓]   [✓]   [✓]   [✓]
ROW5:   [✓]   [✓]   [✓]   [✓]
ROW6:   [✓]   [✓]   [✓]   [✓]
ROW7:   [✓]   [✓]   [✓]   [✓]
```

## Integration with CoreManipulation.py

The MaskEditor now aligns with CoreManipulation.py's `modulesEnabled()` function:

```python
# MaskEditor output format matches CoreManipulation input
masks = {
    "ia_cbb0": "0x00000000",
    "ia_cbb1": "0x00000000",
    "ia_cbb2": "0x00000000",
    "ia_cbb3": "0x00000000",
    "llc_cbb0": "0x00000000",
    "llc_cbb1": "0x00000000",
    "llc_cbb2": "0x00000000",
    "llc_cbb3": "0x00000000"
}

# Direct usage in CoreManipulation
modulesEnabled(moduleslicemask=masks, logical=False, rdfuses=False)
```

## Main Window UI

### Before (3 Compute Buttons)
```
┌──────────────────────────────────────┐
│     System Mask Edit                 │
├──────────────────────────────────────┤
│  [Compute0]  [Compute1]  [Compute2]  │
│         [Save All]  [Cancel]         │
└──────────────────────────────────────┘
```

### After (4 CBB Buttons)
```
┌──────────────────────────────────────────┐
│   DMR CBB Mask Editor                    │
├──────────────────────────────────────────┤
│  [CBB0]  [CBB1]  [CBB2]  [CBB3]          │
│         [Save All]  [Cancel]             │
└──────────────────────────────────────────┘
```

## File Location
[c:\Git\Automation\S2T\BASELINE_DMR\DebugFramework\MaskEditor.py](c:\Git\Automation\S2T\BASELINE_DMR\DebugFramework\MaskEditor.py)
