# MCA Bank Decoder

Product-specific MCA (Machine Check Architecture) bank decoders for DMR, GNR, and CWF products.

## Overview

This module provides comprehensive MCA bank information and decoding utilities for Intel server products:
- **DMR** (Diamond Rapids) - Next-gen architecture with CBB and IMH domains
- **GNR** (Granite Rapids) - Current-gen big core architecture
- **CWF** (Clearwater Forest) - Atom core (E-core) architecture

## Files

### Core Modules
- `dmr/mca_banks.py` - DMR MCA bank definitions (32 banks, CBB + IMH domains)
- `gnr/mca_banks.py` - GNR MCA bank definitions (16+ banks, big core)
- `cwf/mca_banks.py` - CWF MCA bank definitions (15 banks, Atom core)

### Usage Examples
- `mca_decoder_examples.py` - Interactive examples and usage demonstrations

### Integration
- The decoder is automatically integrated into `ErrorReport.py` for enhanced MCA error reporting

## Features

### Bank Information
Each MCA bank decoder provides:
- **Bank ID to Name Mapping**: Quick lookup of bank names
- **Full Descriptive Names**: Complete bank descriptions
- **Scope Information**: Core, Module, Socket, Uncore, IO, CBB, IMH
- **Physical Instance Counts**: How many instances exist per socket/die
- **Merged Bank Info**: Whether multiple physical instances are merged
- **Register Paths**: PysvTools register paths for each bank
- **Additional Notes**: Product-specific details and quirks

### Decoding Functions

All modules provide these standard functions:

```python
# Get bank information
bank_info = mca_banks.get_bank_info(bank_id)

# Get bank name
bank_name = mca_banks.get_bank_name(bank_id)

# Get full descriptive name
full_name = mca_banks.get_bank_full_name(bank_id)

# Decode error with STATUS/ADDR/MISC values
decoded = mca_banks.decode_bank_error(bank_id, status_value=0xBE00000000800150)

# Format human-readable error message
message = mca_banks.format_bank_error(bank_id, register_path='...', status_value=0xBE00...)

# Get banks by scope/domain
core_banks = mca_banks.get_banks_by_scope('Core')
cbb_banks = mca_banks.get_banks_by_domain('CBB')  # DMR only

# Print complete bank table
mca_banks.print_bank_table()
```

## Product-Specific Details

### DMR (Diamond Rapids)

**Architecture**: CBB (Core Building Block) + IMH (Integrated Memory Hub) domains

**Bank Ranges**:
- Banks 0-3: Core-scoped (IFU, DCU, DTLB, MLC)
- Banks 4-8: CBB-scoped (PUNIT, NCU, CCF, D2D, Spare)
- Banks 9-31: IMH-scoped (Memory controllers, interconnects, etc.)

**Special Features**:
- 32 total banks
- Dual-domain architecture (CBB + IMH)
- Merged banks for high instance count IPs
- Sub-channel tracking for memory banks (19-26)
- IMH0 → Domain 0, IMH1 → Domain 1

**Key Banks**:
- Bank 6: CCF (Caching/Coherency Fabric) - 32 instances merged
- Bank 12: HA/MVF (Home Agent) - 16 instances merged
- Banks 19-26: Memory Channels 0-7 with sub-channel merge

### GNR (Granite Rapids)

**Architecture**: Big core (Golden Cove/Raptor Cove) with traditional uncore

**Bank Ranges**:
- Banks 0-3: Core-scoped (IFU, DCU, DTLB, ML2)
- Bank 4+: Uncore, IO, Socket-scoped

**Special Features**:
- 16+ banks
- Big core architecture (2 threads per core)
- PMSB (Power Management State Buffer)
- Variable CHA count based on SKU
- UPI for multi-socket configurations

**Key Banks**:
- Bank 0-3: Core execution units
- Bank 4: PMSB (Power Management State Buffer)
- Bank 5: CHA (Caching and Home Agent)
- Bank 6: IMC (Integrated Memory Controller)
- Bank 10: UPI (Ultra Path Interconnect)

### CWF (Clearwater Forest)

**Architecture**: Atom core (E-core) with 4 cores per module

**Bank Ranges**:
- Banks 0-1: Atom core-scoped (IC, MEC)
- Banks 2-4: Module-scoped (BBL, BUS, L2)
- Bank 5+: Uncore, IO, Socket-scoped

**Special Features**:
- 15 banks
- 4 Atom cores per module
- MEC combines data cache + TLB
- Shared L2 per module
- No PMSB (vs GNR)

**Key Banks**:
- Bank 0: IC (Instruction Cache)
- Bank 1: MEC (Memory Execution Cluster - data cache + TLB)
- Bank 2: BBL (Back-End Logic)
- Bank 3: BUS (Bus Interface Unit)
- Bank 4: L2 (shared by 4 cores)

**Module Architecture**:
- 4 Atom cores per module
- 2 core-scoped banks per core (IC, MEC)
- 3 module-scoped banks (BBL, BUS, L2)
- Total: 11 banks per module

## Integration with ErrorReport.py

The MCA bank decoder is automatically integrated into the error reporting system:

### Automatic Product Detection
```python
# In ErrorReport.py
if SELECTED_PRODUCT == 'GNR':
    from users.gaespino.dev.S2T.product_specific.gnr import mca_banks
elif SELECTED_PRODUCT == 'CWF':
    from users.gaespino.dev.S2T.product_specific.cwf import mca_banks
elif SELECTED_PRODUCT == 'DMR':
    from users.gaespino.dev.S2T.product_specific.dmr import mca_banks
```

### Enhanced MCA Dump Output

When MCA errors are detected, the output now includes:

```
socket0.cbbs.computes.modules.cores[0].ifu_cr_mc0_status = 0xbe00000000800150
 --> MCA Bank 0: IFU (Instruction Fetch Unit)
     Scope: Core | Instruction Fetch Unit errors
--------------------------------------------------------------------------------
```

### Summary Section

The final MCA summary includes full bank decoding:

```
================================================================================
FOUND VALID MCA
================================================================================
socket0.imhs.uncore.ha.mc_status = 0xbe00000000800150
 --> MCA Bank 12: HA_MVF (Home Agent/Memory VF)
     Scope: IMH | Home Agent/Memory Virtual Function errors (merged)
     Note: Merged bank aggregating 16 physical instances
--------------------------------------------------------------------------------
```

## Usage Examples

### Basic Usage

```python
# Import the decoder for your product
from product_specific.dmr import mca_banks

# Get bank information
bank = mca_banks.get_bank_info(6)
print(f"Bank 6: {bank['name']} - {bank['description']}")

# Decode an error
decoded = mca_banks.decode_bank_error(6, status_value=0xBE00000000800150)
print(f"Bank: {decoded['bank_name']}")
print(f"Scope: {decoded['scope']}")
print(f"Valid: {decoded['valid']}")
print(f"Uncorrected: {decoded['uc']}")
```

### In Error Handler

```python
def handle_mca_error(register_path, status_value):
    # Extract bank ID from path (done automatically in decode_mca_bank)
    decoded_info = decode_mca_bank(register_path, status_value)
    
    if decoded_info:
        print(f"MCA Error Detected:")
        print(decoded_info)
        
        # Take action based on bank type
        if 'memory' in decoded_info.lower():
            handle_memory_error()
        elif 'cache' in decoded_info.lower():
            handle_cache_error()
```

### Printing Bank Tables

```python
# Print complete bank table for current product
from product_specific.dmr import mca_banks
mca_banks.print_bank_table()

# Get specific bank groups
core_banks = mca_banks.get_banks_by_scope('Core')
cbb_banks = mca_banks.get_banks_by_domain('CBB')  # DMR
merged_banks = mca_banks.get_merged_banks()  # DMR
```

### Interactive Examples

Run the example script to explore all features:

```bash
python mca_decoder_examples.py
```

This provides interactive examples for all three products with detailed output.

## Benefits

1. **Faster Debug**: Immediately identify what component triggered an MCA
2. **Better Context**: Know the scope and instance count of each bank
3. **Product Awareness**: Understand architecture differences between products
4. **Automation Ready**: Easy integration into automated error analysis
5. **Documentation**: Self-documenting with full descriptions and notes

## Architecture Comparison

| Feature | DMR | GNR | CWF |
|---------|-----|-----|-----|
| Core Type | Atom (E-core) | Big Core (P-core) | Atom (E-core) |
| Cores per Module | 4 | N/A (1 core) | 4 |
| Total Banks | 32 | 16+ | 15 |
| Domains | CBB + IMH | Unified | Unified |
| Core Banks | 0-3 | 0-3 | 0-1 |
| Module Banks | 3 (at CBB) | N/A | 2-4 |
| Memory Banks | 19-26 (8 channels) | 6+ | 6+ |
| PMSB | No | Yes (Bank 4) | No |
| Special Feature | Dual domain, merged banks | Traditional big core | 4 cores/module, MEC |

## Notes

- The decoder automatically handles product-specific differences
- Bank IDs may not be sequential in all products
- Some banks are reserved for future use
- Merged banks aggregate multiple physical instances
- CWF's MEC combines functionality of GNR's DCU + DTLB

## Future Enhancements

Potential additions:
- MCACOD (MCA error code) decoding per bank
- Field-level MCi_STATUS/MISC/ADDR decoding
- Error signature matching
- Historical error tracking
- Integration with automated bucketing

## Author

gaespino  
Last Updated: November 12, 2025
