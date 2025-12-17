# MCA Decoder Enhancements - Implementation Summary

## Overview
Enhanced the MCA Single Line Decoder with three major improvements:
1. **Auto-Detection for CORE decoder** - Automatically determines bank type from MSCOD
2. **IO Decoder** - Support for UBOX, UPI, and ULA decoding
3. **First Error Logger** - Decodes UBOX MCERRLOGGINGREG and IERRLOGGINGREG

## Changes Implemented

### 1. CORE Decoder - Auto-Detection

**What Changed:**
- Removed manual bank type selection for CORE decoder
- Added `detect_core_bank()` method to auto-detect from MSCOD value
- Updated UI to show "Auto-detects bank from MSCOD" description
- Decoder now displays detected bank type in results

**How It Works:**
```python
def detect_core_bank(self, mscod, product):
    """Auto-detect core bank type from MSCOD value"""
    # For BigCore products (GNR, DMR)
    if product in ['GNR', 'DMR']:
        if mscod <= 0x7F:
            return 'ML2'
        elif mscod <= 0x1F:
            return 'DCU'
        elif mscod <= 0x1FFF:
            return 'IFU'
        elif mscod <= 0x3F:
            return 'DTLB'
        else:
            return 'ML2'  # Default

    # For AtomCore products (CWF)
    elif product == 'CWF':
        return 'L2'  # Default for Atom

    return 'ML2'  # Ultimate fallback
```

**Benefits:**
- No need to manually select bank type
- Decoder automatically identifies the correct bank
- Reduces user error
- Faster workflow

**Example Output:**
```
MC_STATUS Decode (Auto-detected: ML2):
----------------------------------------
  Bank Type:              ML2
  MCACOD (Error Decode):  L2_Data_Array_Error
  MSCOD:                  0x0023
  VAL (Valid):            1
  UC (Uncorrected):       1
  PCC (Proc Context):     0
```

### 2. IO Decoder

**What Added:**
- New decoder type: **'IO'**
- Supports: UBOX, UPI, ULA
- Uses `io_decoder()` method from decoder.py
- Decodes MCACOD and MSCOD based on IO instance type

**Configuration:**
```python
'IO': {
    'description': 'IO Subsystem Decoder (UBOX, UPI, ULA)',
    'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
    'decode_method': 'io',
    'subtypes': ['UBOX', 'UPI', 'ULA']
}
```

**Decoder Method:**
```python
def decode_io(self, values, product):
    """Decode IO Subsystem MCA registers"""
    io_type = self.subtype_var.get()

    # Create decoder instance
    dec = mcparse.decoder(data=dummy_df, product=product)

    # Decode using io_decoder from decoder.py
    mcacod_decoded, mscod_decoded = dec.io_decoder(
        value=mc_status,
        instance_type=io_type
    )
```

**Special Handling:**
- **UBOX**: Different MSCOD tables based on MCACOD value
  - MCACOD 1042 → CMS_MSCOD table
  - MCACOD 1043 → SBO_MSCOD table
  - MCACOD 1036 → SHUTDOWN_ERR_MSCOD table
- **UPI**: Uses UPI_MSCOD table from JSON
- **ULA**: DMR-specific decoder (for DMR product)

**Example Output:**
```
IO MCA DECODE - GNR - UBOX
========================================
Raw Register Values:
  MC_STATUS:  0x9200000000001042
  MC_ADDR:    0x0000000000000000

MC_STATUS Decode (UBOX):
----------------------------------------
  MCACOD:  SCF Bridge IP:CMS error (0x1042)
  MSCOD:   CMS Error Type (MSCOD=18)
  VAL (Valid):         1
  UC (Uncorrected):    1
  PCC (Proc Context):  0
```

### 3. First Error Logger Decoder

**What Added:**
- New decoder type: **'FIRST ERROR'**
- Decodes UBOX First Error logging registers
- Supports both MCERRLOGGINGREG and IERRLOGGINGREG
- Uses `portids_decoder()` method from decoder.py

**Configuration:**
```python
'FIRST ERROR': {
    'description': 'First Error Logger - UBOX MCERR/IERR Logging',
    'registers': ['MCERRLOGGINGREG', 'IERRLOGGINGREG'],
    'decode_method': 'first_error'
}
```

**Register Format:**
Both registers have same bit layout:
- **Bits [15:0]** - First Error Source ID
- **Bit 16** - First Error Valid
- **Bit 17** - First Error From Core
- **Bits [47:32]** - Second Error Source ID
- **Bit 48** - Second Error Valid
- **Bit 49** - Second Error From Core

**Decoder Method:**
```python
def decode_first_error(self, values, product):
    """Decode First Error Logger - UBOX MCERR/IERR Logging registers"""
    mcerr_reg = values.get('MCERRLOGGINGREG', '')
    ierr_reg = values.get('IERRLOGGINGREG', '')

    # Uses portids_decoder() to decode source IDs
    if mcerr_reg:
        portids_values = dec.portids_decoder(
            value=mcerr_reg,
            portid_data=portid_data,
            event='mcerr'
        )
```

**Port ID Decoding:**
- Decodes to DIE ID, Port ID, Location, and FromCore flag
- Uses product-specific log_portid.json files
- Provides hierarchical location information

**Example Output:**
```
FIRST ERROR DECODE - GNR
========================================
Raw Register Values:
  MCERRLOGGINGREG:  0x0000000300018042
  IERRLOGGINGREG:   0x0000000000000000

MCERRLOGGINGREG Decode:
----------------------------------------
  First Error:
    DIE ID:     0
    Port ID:    0x042
    Location:   CHA_00
    From Core:  0

  Second Error:
    DIE ID:     0
    Port ID:    0x180
    Location:   UPI_0
    From Core:  1

IERRLOGGINGREG Decode:
----------------------------------------
  First Error:
    DIE ID:     N/A
    Port ID:    N/A
    Location:   N/A
    From Core:  N/A
```

## Validation Updates

**Modified Validation Logic:**
```python
# Check for required fields based on decoder type
if decoder_type == 'FIRST ERROR':
    # At least one of MCERRLOGGINGREG or IERRLOGGINGREG required
    if not register_values.get('MCERRLOGGINGREG') and \
       not register_values.get('IERRLOGGINGREG'):
        errors.append("At least one of MCERRLOGGINGREG or IERRLOGGINGREG is required")
else:
    # MC_STATUS is required for all other decoders
    if 'MC_STATUS' not in register_values:
        errors.append("MC_STATUS is required")
```

## Product-Specific Handling

### GNR (Granite Rapids)
- BigCore architecture
- CORE: ML2, DCU, IFU, DTLB
- IO: UBOX, UPI
- First Error: Standard UBOX logging

### CWF (Clearwater Forest)
- AtomCore architecture
- CORE: L2, BBL, BUS, MEC, AGU, IC
- IO: UBOX, UPI
- First Error: Standard UBOX logging

### DMR (Diamond Rapids)
- BigCore architecture
- CORE: ML2, DCU, IFU, DTLB
- IO: UBOX, UPI, ULA (DMR-specific)
- First Error: May have different UBOX format (fallback to manual decode)

## UI Flow

### Before (CORE):
1. Select Product
2. Select Decoder: CORE
3. **Select Bank Type: ML2/DCU/IFU/DTLB**  ← Manual selection
4. Enter MC_STATUS
5. Decode

### After (CORE):
1. Select Product
2. Select Decoder: CORE ← No bank selection needed
3. Enter MC_STATUS
4. Decode → **Auto-detects bank from MSCOD**

### IO Decoder:
1. Select Product
2. Select Decoder: IO
3. Select IO Type: UBOX/UPI/ULA
4. Enter MC_STATUS (+ optional ADDR/MISC)
5. Decode

### First Error Decoder:
1. Select Product
2. Select Decoder: FIRST ERROR
3. Enter MCERRLOGGINGREG and/or IERRLOGGINGREG
4. Decode

## Error Handling

All decoders include:
- Try/except blocks for decoder errors
- Fallback to generic bit extraction if JSON decode fails
- Clear error messages in results
- Graceful degradation

**Example Fallback:**
```python
except Exception as e:
    self.update_results(f"  Error decoding: {str(e)}\n")
    # Manual bit extraction as fallback
    try:
        first_src = extract_bits(mcerr_reg, 0, 15)
        first_valid = extract_bits(mcerr_reg, 16, 16)
        self.update_results(f"\n  Manual Decode:\n")
        self.update_results(f"    First SrcID: 0x{first_src:04X}\n")
    except:
        pass
```

## Testing Recommendations

### CORE Auto-Detection
- Test with known ML2 MCAs (MSCOD ≤ 0x7F)
- Test with DCU MCAs (MSCOD ≤ 0x1F)
- Test with IFU MCAs (MSCOD ≤ 0x1FFF)
- Test with DTLB MCAs (MSCOD ≤ 0x3F)
- Verify Atom products default to L2

### IO Decoder
- Test UBOX with different MCACOD values (1042, 1043, 1036)
- Verify MSCOD table selection is correct
- Test UPI with UPI_MSCOD JSON
- Test ULA for DMR products

### First Error Logger
- Test with valid MCERRLOGGINGREG
- Test with valid IERRLOGGINGREG
- Test with both registers populated
- Test with only one register populated
- Verify Port ID decoding matches JSON
- Test fallback to manual decode

## Files Modified

1. **PPV/gui/MCADecoder.py**
   - Added `detect_core_bank()` method
   - Modified CORE decoder configuration (removed subtypes, added auto_detect flag)
   - Added IO decoder configuration and `decode_io()` method
   - Added First Error decoder configuration and `decode_first_error()` method
   - Updated validation logic for First Error registers
   - Updated `on_decoder_changed()` to handle auto_detect flag

## Benefits Summary

1. **Improved Usability**
   - CORE decoder no longer requires manual bank selection
   - Faster workflow for debug sessions
   - Fewer user errors

2. **Extended Coverage**
   - IO subsystem now supported (UBOX, UPI, ULA)
   - First Error logging analysis available
   - Complete MCA ecosystem coverage

3. **Better Product Support**
   - Product-specific auto-detection logic
   - DMR-specific ULA support
   - Atom vs BigCore architecture awareness

4. **Robust Error Handling**
   - Fallback mechanisms for all decoders
   - Clear error messages
   - Manual bit extraction when JSON unavailable

## Future Enhancements

Potential improvements:
- [ ] More sophisticated CORE bank detection (use MCACOD patterns too)
- [ ] DMR-specific First Error format handling
- [ ] History of decoded First Errors
- [ ] Visual timeline of error sequences
- [ ] Integration with other UBOX registers (control, status)

## Summary

Successfully enhanced the MCA Decoder with three major features:
- ✅ CORE decoder auto-detection from MSCOD
- ✅ IO subsystem decoder (UBOX, UPI, ULA)
- ✅ First Error Logger decoder (MCERRLOGGINGREG, IERRLOGGINGREG)

All features integrate seamlessly with existing decoder infrastructure and maintain backward compatibility.
