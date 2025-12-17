# MCA Single Line Decoder

## Overview

The MCA Single Line Decoder is an interactive GUI tool for decoding individual Machine Check Architecture (MCA) register values. This tool provides real-time decoding capabilities for various IP blocks across multiple Intel products.

## Features

- **Multi-Product Support**: GNR, CWF, and DMR
- **Multiple Decoder Types**:
  - CHA/CCF (Caching Agent / CCF)
  - LLC (Last Level Cache)
  - CORE (CPU Core - ML2, DCU, IFU, DTLB, etc.)
  - MEMORY (Memory Subsystem - B2CMI, MSE, MCCHAN)
- **Dynamic Fields**: Input fields adapt based on selected decoder type
- **Real-Time Decoding**: Instant decode results with detailed explanations
- **Status Bit Analysis**: Automatic decoding of VAL, UC, PCC, ADDRV, MISCV bits

## Usage

### Launching the Tool

From PPV Tools Hub:
```python
# Launch from PPV Tools main menu
python PPV/gui/PPVTools.py
# Click on "MCA Decoder" card
```

Standalone:
```python
# Run directly
python PPV/gui/MCADecoder.py
```

### Decoding Process

1. **Select Product**: Choose from GNR, CWF, or DMR
2. **Select Decoder Type**: Choose the appropriate decoder:
   - CHA/CCF for caching agent errors
   - LLC for last level cache errors
   - CORE for CPU core errors
   - MEMORY for memory subsystem errors
3. **Select Bank/Type** (if applicable): For CORE and MEMORY decoders
4. **Input Register Values**: Enter hex values for:
   - MC_STATUS (required)
   - MC_ADDR (optional)
   - MC_MISC (optional)
   - MC_MISC3 (optional for CHA/CCF)
5. **Click "Decode MCA"**: View detailed decode results

### Input Format

Register values can be entered in the following formats:
- With 0x prefix: `0x9C00000040000000`
- Without prefix: `9C00000040000000`
- Case insensitive

### Example Decode

**Input:**
- Product: GNR
- Decoder: CHA/CCF
- MC_STATUS: `0x9C00000040000000`
- MC_MISC: `0x0000000000000080`

**Output:**
```
CHA/CCF MCA DECODE - GNR
========================================
Raw Register Values:
  MC_STATUS:  0x9C00000040000000
  MC_MISC:    0x0000000000000080

MC_STATUS Decode:
  MSCOD (Error Type):  MSCOD_UNCORRECTABLE_TAG_ERROR
  VAL (Valid):         1 (Valid)
  UC (Uncorrected):    1 (Uncorrected)
  PCC (Proc Context):  0 (Not Corrupted)
  ADDRV (Addr Valid):  1 (Valid)
  MISCV (Misc Valid):  1 (Valid)

MC_MISC Decode:
  Original Request:  RdCode
  Opcode:            DRd
  Cache State:       I
  TOR ID:            10
  TOR FSM:           3
```

## Decoder Types Details

### CHA/CCF Decoder
Decodes Caching and Home Agent (CHA) and Common Coherence Fabric (CCF) errors:
- MSCOD error types
- TOR opcodes and states
- Cache states
- Source/Destination IDs
- FSM states

### LLC Decoder
Decodes Last Level Cache errors:
- LLC-specific MSCOD values
- RSF/LSF state information
- Cache line states

### CORE Decoder
Decodes CPU core MCA banks:
- **BigCore**: ML2, DCU, IFU, DTLB
- **AtomCore**: L2, BBL, BUS, MEC, AGU, IC
- MCACOD and MSCOD decoding
- PCC (Processor Context Corrupted) analysis

### MEMORY Decoder
Decodes memory subsystem errors:
- B2CMI (Bus-to-CMI) errors
- MSE (Memory Security Engine) errors
- MCCHAN (Memory Channel) errors

## Architecture

### Key Components

1. **MCADecoderGUI**: Main GUI class
2. **Product Configuration**: Dynamic field generation
3. **Decoder Integration**: Uses existing decoder.py infrastructure
4. **Bit Extraction**: Leverages extract_bits() utility

### Decoder Method Mapping

```python
decoder_types = {
    'CHA/CCF': {
        'decode_method': 'cha',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC', 'MC_MISC3']
    },
    'LLC': {
        'decode_method': 'llc',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC']
    },
    'CORE': {
        'decode_method': 'core',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
        'subtypes': ['ML2', 'DCU', 'IFU', 'DTLB', ...]
    },
    'MEMORY': {
        'decode_method': 'mem',
        'registers': ['MC_STATUS', 'MC_ADDR', 'MC_MISC'],
        'subtypes': ['B2CMI', 'MSE', 'MCCHAN']
    }
}
```

## Benefits

- **No File Required**: Decode single MCAs without full DPMB data files
- **Quick Analysis**: Fast decode for debug sessions
- **Educational**: Understand MCA register bit fields
- **Reuses Infrastructure**: Leverages existing decoder JSON files and logic
- **Minimal Code Changes**: No modifications to existing decoder.py

## Technical Details

### Dependencies
- tkinter (GUI)
- pandas (for decoder initialization)
- Decoder module (decoder.py, extract_bits)
- Product-specific JSON decode files

### Decoder Initialization
Creates minimal pandas DataFrame for decoder instantiation:
```python
dummy_df = pd.DataFrame({
    'VisualId': [1],
    'TestName': ['dummy'],
    'TestValue': ['0x0']
})
dec = mcparse.decoder(data=dummy_df, product=product)
```

### Bit Field Extraction
Uses standard extract_bits() function:
```python
from Decoder.decoder import extract_bits

val_bit = extract_bits(hex_value, 63, 63)  # Extract bit 63
mscod = extract_bits(hex_value, 16, 31)     # Extract bits 16-31
```

## Future Enhancements

Potential improvements:
- [ ] Save/Load decode sessions
- [ ] Export decode results to file
- [ ] Batch decode multiple MCAs
- [ ] History of decoded values
- [ ] Copy decode results to clipboard
- [ ] Compare two MCAs side-by-side
- [ ] Integration with telemetry capture tools

## Troubleshooting

### Common Issues

1. **"Failed to initialize decoder"**
   - Ensure product JSON files exist in `Decoder/<PRODUCT>/` folder
   - Check that decoder.py is accessible

2. **"Invalid hex format"**
   - Verify hex values are properly formatted
   - Ensure no special characters except 0x prefix

3. **"N/A" in decode results**
   - Value not found in decode dictionary
   - May indicate reserved or product-specific encoding

4. **Empty decoder results**
   - Check that appropriate decoder type is selected
   - Verify MC_STATUS is provided (required field)

## Contact

For issues or enhancements, contact the PPV Tools development team.
