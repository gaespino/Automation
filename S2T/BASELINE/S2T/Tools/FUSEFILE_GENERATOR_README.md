# FuseFileGenerator Class

## Overview
The `FuseFileGenerator` class converts register arrays into fuse configuration files compatible with the `fusefilegen.py` parser. This is the **inverse operation** of `fusefilegen` - instead of reading a fuse file to get register arrays, it creates fuse files from register arrays.

**Multi-Product Support**: The class accepts product-specific fusefilegen modules as parameters, supporting GNR, DMR, CWF, and any future products.

## Purpose
When working with register dumps or programmatically generated register configurations, you may have an array of fully-qualified register assignments that need to be formatted as a fuse file for use with product-specific tooling.

## Usage

### Basic Example
```python
from S2T.Tools.registerdump import FuseFileGenerator
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen

# Your register array (from register dump, script, etc.)
register_array = [
    'sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa',
    'sv.socket0.compute1.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa',
    'sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point1= 0xb1',
]

# Create generator and generate fuse file
generator = FuseFileGenerator(gnr_fusefilegen, register_array, product='gnr')
generator.create_fuse_file()
# Output: C:\Temp\RegisterDumpLogs\2026-02-17_143022_generated.fuse
```

### DMR Product Example
```python
from S2T.product_specific.dmr import fusefilegen as dmr_fusefilegen

# DMR has different hierarchy (cbb, imh)
dmr_array = [
    'sv.socket0.cbb0.base.fuses.pcu.config_register1= 0x10',
    'sv.socket0.cbb0.compute0.fuses.pcu.compute_config= 0x20',
    'sv.socket0.imh0.fuses.memory.timing_register= 0x30',
]

generator = FuseFileGenerator(dmr_fusefilegen, dmr_array, product='dmr')
generator.create_fuse_file()
```

### CWF Product Example
```python
from S2T.product_specific.cwf import fusefilegen as cwf_fusefilegen

# CWF uses same hierarchy as GNR
cwf_array = [
    'sv.socket0.compute0.fuses.pcie.config_lane0= 0xA1',
    'sv.socket0.io0.fuses.pcie.link_config= 0xB2',
]

generator = FuseFileGenerator(cwf_fusefilegen, cwf_array, product='cwf')
generator.create_fuse_file()
```

### Custom Output Path
```python
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen

# Specify custom output file
generator = FuseFileGenerator(
    gnr_fusefilegen,
    register_array,
    product='gnr',
    output_file=r"C:\MyProject\fuses\custom_config.fuse"
)
generator.create_fuse_file()
```

### Step-by-Step Process
```python
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen

generator = FuseFileGenerator(gnr_fusefilegen, register_array, product='gnr')

# Step 1: Parse and validate the array
if generator.parse_array():
    print(f"Parsed {len(generator.parsed_data)} sections")

    # Step 2: Generate the file
    if generator.generate_fuse_file():
        print(f"File created: {generator.fuse_file_path}")
```

### Get Detailed Report
```python
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen

generator = FuseFileGenerator(gnr_fusefilegen, register_array, product='gnr')
generator.create_fuse_file()

report = generator.get_report()
print(f"Product: {generator.product.upper()}")
print(f"Sections: {report['section_count']}")
print(f"Registers: {report['register_count']}")
print(f"Errors: {report['errors']}")
print(f"Warnings: {report['warnings']}")
print(f"Output file: {report['output_file']}")
```

## Input Format

### GNR / CWF Format
The register array should contain fully-qualified register assignments:
```
sv.socket<N>.compute<N>.fuses.<register_path> = <value>
sv.socket<N>.io<N>.fuses.<register_path> = <value>
sv.sockets.computes.fuses.<register_path> = <value>  # Applies to all
sv.sockets.ios.fuses.<register_path> = <value>       # Applies to all
```

### DMR Format
```
sv.socket<N>.cbb<N>.base.fuses.<register_path> = <value>
sv.socket<N>.cbb<N>.compute<N>.fuses.<register_path> = <value>
sv.socket<N>.imh<N>.fuses.<register_path> = <value>
sv.sockets.cbbs.base.fuses.<register_path> = <value>  # Applies to all
sv.sockets.cbbs.computes.fuses.<register_path> = <value>
sv.sockets.imhs.fuses.<register_path> = <value>
```

## Output Format
The generated fuse file follows the INI-like format expected by `fusefilegen.py`:
```ini
# Fuse file generated from register array
# Generated on: 2026-02-17 14:30:22

[sv.socket0.compute0.fuses]
pcu.pcode_ddrd_ddr_vf_voltage_point0 = 0xaa
pcu.pcode_ddrd_ddr_vf_voltage_point1 = 0xb1

[sv.socket0.compute1.fuses]
pcu.pcode_ddrd_ddr_vf_voltage_point0 = 0xaa
```

## Supported Products and Hierarchies

### GNR (Granite Rapids)
- `sv.socket<N>.compute<N>.fuses` - Specific socket and compute
- `sv.socket<N>.io<N>.fuses` - Specific socket and IO
- `sv.sockets.computes.fuses` - All sockets, all computes
- `sv.sockets.ios.fuses` - All sockets, all IOs

### DMR (Diamond Rapids)
- `sv.socket<N>.cbb<N>.base.fuses` - Specific socket, cbb base
- `sv.socket<N>.cbb<N>.compute<N>.fuses` - Specific socket, cbb, and compute
- `sv.socket<N>.imh<N>.fuses` - Specific socket and IMH
- `sv.sockets.cbbs.base.fuses` - All sockets, all cbbs base
- `sv.sockets.cbbs.computes.fuses` - All sockets, cbbs, computes
- `sv.sockets.imhs.fuses` - All sockets, all IMHs

### CWF (Clearwater Forest)
- Same hierarchy as GNR (compute/io based)

**Note**:
- `<N>` = Specific number (0, 1, 2, ...)
- `s` suffix = Plural form (applies to all units)

## Features
- **Multi-Product Support**: Works with GNR, DMR, CWF, and extensible to future products
- **Flexible Module Loading**: Accepts product-specific fusefilegen modules as parameters
- **Automatic Parsing**: Extracts sections and registers from full paths
- **Validation**: Validates against product-specific hierarchy patterns
- **Duplicate Detection**: Warns about duplicate registers
- **Sorted Output**: Sections and registers are alphabetically sorted
- **Error Reporting**: Detailed error and warning messages
- **Timestamp**: Auto-generated filenames with timestamps
- **Compatible**: Output format matches `fusefilegen.py` input format

## Error Handling
The class provides detailed error and warning messages:
- Invalid entry format (missing `=`)
- Invalid section patterns for the specified product
- Empty register names
- Duplicate registers (overwrites with warning)
- Missing FuseFileParser class or VALID_SECTION_PATTERNS in provided module

```python
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen

generator = FuseFileGenerator(gnr_fusefilegen, invalid_array, product='gnr')
if not generator.create_fuse_file():
    for error in generator.errors:
        print(f"ERROR: {error}")
    for warning in generator.warnings:
        print(f"WARNING: {warning}")
```

## Integration with RegisterDump
The `FuseFileGenerator` class is part of the `registerdump.py` module and reuses common infrastructure:
- Same default output directory (`C:\Temp\RegisterDumpLogs`)
- Consistent timestamp formatting
- Similar error handling patterns
- Product support through passing fusefilegen module as parameter

## Examples
See [fusefile_generator_example.py](fusefile_generator_example.py) for comprehensive examples including:
1. Auto-generated file with default naming (GNR)
2. DMR product with different hierarchy
3. CWF product
4. Step-by-step parsing and generation
5. Working with IO fuses
6. Using plural sections (sockets/computes)

## Verification
The generated fuse file can be verified by reading it back with product-specific `fusefilegen.py`:

### GNR Verification
```python
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen
from S2T.product_specific.gnr.fusefilegen import process_fuse_file

# Generate fuse file from array
generator = FuseFileGenerator(gnr_fusefilegen, register_array, product='gnr')
generator.create_fuse_file()

# Verify by reading it back
registers = process_fuse_file(generator.fuse_file_path)
print(registers)  # Should match original array (order may differ)
```

### DMR Verification
```python
from S2T.product_specific.dmr import fusefilegen as dmr_fusefilegen
from S2T.product_specific.dmr.fusefilegen import process_fuse_file

generator = FuseFileGenerator(dmr_fusefilegen, dmr_array, product='dmr')
generator.create_fuse_file()
registers = process_fuse_file(generator.fuse_file_path)
```

## Adding New Products
The class automatically supports new products when you:
1. Create a new fusefilegen module: `S2T.product_specific.<product>/fusefilegen.py`
2. Define `FuseFileParser` class with `VALID_SECTION_PATTERNS` attribute
3. Import the module and pass it when creating the generator:
   ```python
   from S2T.product_specific.<product> import fusefilegen as <product>_fusefilegen
   generator = FuseFileGenerator(<product>_fusefilegen, array, product='<product>')
   ```

No changes to `registerdump.py` are required - the module is passed directly as a parameter.
