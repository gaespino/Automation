# Fuse File Generator Tool

## Overview

The Fuse File Generator (`fusefilegen.py`) is a tool for parsing user-created fuse configuration files and generating arrays of fully-qualified register paths for use with CoreManipulation. Each product (DMR, GNR, CWF) has its own version with product-specific hierarchy validation.

## File Format

The tool uses a **custom INI-like format** with native hex support:
- Easy to read and write for users
- **Native hex notation**: Write `0xFF` directly without quotes
- Simple and intuitive syntax
- Preserves values exactly as written
- Perfect for fuse configurations

### Format Rules

1. **Sections** are defined in brackets: `[sv.socket0.compute0.fuses]`
2. **Registers** are defined as key-value pairs: `register_name = 0x1`
3. **Full paths** can be used in register names: `sv.socket0.compute0.fuses.register = 0xFF`
   - If a full path starting with `sv.` is used, it won't be duplicated
4. **Comments** start with `#`
5. **Hex values** are written directly: `0xFF`, `0xDEADBEEF` (no quotes needed)
6. **Values** are kept exactly as written in the output

## Product-Specific Hierarchies

### DMR Product

**Location:** `S2T/product_specific/dmr/fusefilegen.py`

**Hierarchy:**
- `sv.socket<N>.cbb<N>.base.fuses` - Specific socket and CBB base
- `sv.socket<N>.cbb<N>.compute<N>.fuses` - Specific socket, CBB, and compute (top)
- `sv.socket<N>.imh<N>.fuses` - Specific socket and IMH
- `sv.sockets.cbbs.base.fuses` - All sockets, all CBBs base
- `sv.sockets.cbbs.computes.fuses` - All sockets, all CBBs, all computes
- `sv.sockets.imhs.fuses` - All sockets, all IMHs

**Example:**
```ini
[sv.socket0.cbb0.base.fuses]
register1 = 0x1
register2 = 0x2

[sv.sockets.cbbs.base.fuses]
common_reg = 0xFF

[sv.socket0.cbb0.compute0.fuses]
compute_reg = 0x10

[sv.socket0.imh0.fuses]
imh_reg = 0x100
```

### GNR Product

**Location:** `S2T/product_specific/gnr/fusefilegen.py`

**Hierarchy:**
- `sv.socket<N>.compute<N>.fuses` - Specific socket and compute
- `sv.socket<N>.io<N>.fuses` - Specific socket and IO
- `sv.sockets.computes.fuses` - All sockets, all computes
- `sv.sockets.ios.fuses` - All sockets, all IOs

**Example:**
```ini
[sv.socket0.compute0.fuses]
registerx1 = 0x1
registerx2 = 0x2

[sv.sockets.computes.fuses]
common_reg = 0xFF

[sv.socket0.io0.fuses]
io_reg = 0x10
```

### CWF Product

**Location:** `S2T/product_specific/cwf/fusefilegen.py`

**Hierarchy:** Same as GNR
- `sv.socket<N>.compute<N>.fuses` - Specific socket and compute
- `sv.socket<N>.io<N>.fuses` - Specific socket and IO
- `sv.sockets.computes.fuses` - All sockets, all computes
- `sv.sockets.ios.fuses` - All sockets, all IOs

## Usage

### Command Line

```bash
# Basic usage - validate and generate output to stdout
python fusefilegen.py <input_file>

# Validate only (no output generation)
python fusefilegen.py <input_file> --validate-only

# Generate output to file
python fusefilegen.py <input_file> -o output.txt

# Different output formats
python fusefilegen.py <input_file> --format list    # One per line (default)
python fusefilegen.py <input_file> --format python  # Python list
python fusefilegen.py <input_file> --format json    # JSON array
```

### Python API

```python
from pathlib import Path

# For DMR
from S2T.product_specific.dmr.fusefilegen import DMRFuseFileParser

parser = DMRFuseFileParser()
if parser.parse_file(Path('fuses.ini')):
    registers = parser.generate_register_list()
    print(registers)
else:
    print(parser.errors)

# For GNR
from S2T.product_specific.gnr.fusefilegen import GNRFuseFileParser

parser = GNRFuseFileParser()
if parser.parse_file(Path('fuses.ini')):
    registers = parser.generate_register_list()

# For CWF
from S2T.product_specific.cwf.fusefilegen import CWFFuseFileParser

parser = CWFFuseFileParser()
if parser.parse_file(Path('fuses.ini')):
    registers = parser.generate_register_list()
```

## Output Format

The tool generates a list of fully-qualified register assignments:

```python
[
    "sv.socket0.cbb0.base.fuses.register1=0x1",
    "sv.socket0.cbb0.base.fuses.register2=0x2",
    "sv.sockets.cbbs.base.fuses.common_reg=0xFF",
    # ... etc
]
```

## Examples

Example files are provided for each product:
- `S2T/product_specific/dmr/example_dmr_fuses.fuse`
- `S2T/product_specific/gnr/example_gnr_fuses.fuse`
- `S2T/product_specific/cwf/example_cwf_fuses.fuse`

### Running Examples

```bash
# DMR example
cd S2T/product_specific/dmr
python fusefilegen.py example_dmr_fuses.fuse

# GNR example
cd S2T/product_specific/gnr
python fusefilegen.py example_gnr_fuses.fuse

# CWF example
cd S2T/product_specific/cwf
python fusefilegen.py example_cwf_fuses.fuse
```

## Validation

The tool validates:
1. **File format** - Must have valid INI-like syntax
2. **Section names** - Must match product-specific hierarchy patterns
3. **Duplicate prevention** - Avoids duplicate register assignments

### Common Errors

**Invalid section name:**
```
ERROR: Invalid section 'sv.socket0.bad.fuses'. Must match DMR hierarchy: ...
```
Fix: Use correct hierarchy pattern for your product

**Parse error:**
```
ERROR: Line 10: Key-value pair outside of section
```
Fix: Ensure all key-value pairs are under a section header `[section.name]`

**Invalid syntax:**
```
ERROR: Line 15: Invalid syntax
```
Fix: Ensure lines follow format: `key = value` or `[section]`

## Integration with CoreManipulation

The generated register list can be passed directly to CoreManipulation:

```python
from S2T.product_specific.dmr.fusefilegen import DMRFuseFileParser
from S2T.CoreManipulation import CoreManipulation

# Parse fuse file
parser = DMRFuseFileParser()
parser.parse_file(Path('my_fuses.fuse'))
registers = parser.generate_register_list()

# Use with CoreManipulation
cm = CoreManipulation()
for register in registers:
    reg_path, value = register.split('=')
    # Apply register setting
    cm.set_register(reg_path, value)
```

## Dependencies

**No external dependencies required!** The tool uses only Python standard library.

## File Format Comparison

### Why Custom INI Format?

**Problem with standard formats:**
- ❌ **JSON**: No hex literal support - must use `255` or `"0xFF"` (strings)
- ❌ **TOML**: No hex literal support - must use `255` or `"0xFF"` (strings)
- ❌ **Standard INI**: No clear specification, limited parsing

**Our Solution:**
✅ **Custom INI with hex support** - Write hex values naturally!

**Comparison:**

**JSON (requires quotes for hex):**
```json
{
  "sv.socket0.cbb0.base.fuses": {
    "register1": "0x1",
    "register2": "0x2"
  }
}
```

**TOML (requires quotes for hex):**
```toml
["sv.socket0.cbb0.base.fuses"]
register1 = "0x1"
register2 = "0x2"
```

**Our Format (native hex support):**
```ini
[sv.socket0.cbb0.base.fuses]
register1 = 0x1
register2 = 0xFF
register3 = 0xDEADBEEF
```

## Tips

1. **Comments** - Use `#` to add notes in your config files
2. **Organization** - Group related registers in sections
3. **Validation** - Always run with `--validate-only` first to check syntax
4. **Full paths** - When register names might be ambiguous, use full paths
5. **Hex values** - Write hex values naturally: `0xFF`, `0xDEAD`, `0x123ABC`
6. **Simple syntax** - Just `[section]` and `key = value` - that's it!

## Troubleshooting

### Issue: "Key-value pair outside of section"
**Solution:** Ensure all registers are under a section header: `[sv.socket0.compute0.fuses]`

### Issue: "Invalid section name"
**Solution:** Check that your section matches the product hierarchy (see hierarchies above)

### Issue: Duplicate registers
**Solution:** The tool automatically handles duplicates - only unique entries are kept

### Issue: Wrong output format
**Solution:** Use `--format` flag to specify desired format (list, python, json)

### Issue: "Invalid syntax"
**Solution:** Ensure each line is either a comment `#`, section `[name]`, or key-value `key = value`
