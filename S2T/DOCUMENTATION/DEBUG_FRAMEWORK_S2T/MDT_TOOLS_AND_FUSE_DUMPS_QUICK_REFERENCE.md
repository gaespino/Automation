# MDT Tools & Fuse Dumps - Quick Reference Guide

**Version:** 1.7+
**Release Date:** February 16, 2026
**Products:** DMR (Primary), GNR/CWF (Limited)
**Maintainer:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

---

## Overview

Version 1.7+ introduces powerful debug capabilities for register analysis and hardware debugging.

### New Features

- **MDT Tools Interface** - Access debug module components for advanced hardware analysis
- **TOR Dumps** - Generate Transaction Ordering Ring dumps from CCF
- **Fuse/Register Dumps** - Complete register value exports for analysis and comparison

---

## MDT Tools Interface

### Quick Start - TOR Dump

```python
import S2T.dpmChecks as dpm

# Generate TOR dump (simplest method)
dpm.tor_dump()
# Output: C:\Temp\tor_dump_<timestamp>.xlsx

# With custom path and ID
dpm.tor_dump(
    destination_path='C:\\Debug',
    visual_id='GNRAP_U0042_test1'
)
# Output: C:\Debug\tor_dump_GNRAP_U0042_test1_<timestamp>.xlsx
```

### Advanced Usage

```python
# Initialize MDT tools
mdt = dpm.mdt_tools()

# Check available components
mdt.print_available_components()

# Access components directly
if mdt.ccf:
    tor_valid = mdt.ccf.get_cbos_tor_trk_valid()
    tor_dump = mdt.ccf.get_cbos_tor_dump()
```

### Available Components

| Component | Purpose | Availability |
|-----------|---------|--------------|
| `ccf` | CCF/CHA analysis, TOR dumps | All products |
| `pm` | Power management | DMR |
| `xbar` | Crossbar analysis | DMR |
| `cache` | Cache analysis | DMR, GNR/CWF |
| `fivr` | Voltage regulator | DMR |

### Performance

| Init Type | Time | Use Case |
|-----------|------|----------|
| TOR dump only | 5-10s | Quick debugging |
| All components | 30-60s | Full system analysis |

---

## Fuse/Register Dumps

### Quick Start

```python
import S2T.dpmChecks as dpm

# DMR - Dump CBB0 fuses
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\cbb0_dump.csv'
)

# GNR/CWF - Dump compute0 fuses
dpm.fuse_dump(
    base=sv.socket0.compute0.fuses,
    file_path='C:\\Temp\\compute0_dump.csv'
)
```

### Dump Multiple Dies

```python
# DMR - All CBBs
for cbb in sv.socket0.cbbs:
    path = f'C:\\Temp\\{cbb.name}_dump.csv'
    dpm.fuse_dump(base=cbb.base.fuses, file_path=path)
    print(f"Dumped {cbb.name}")

# GNR/CWF - All computes
for compute in sv.socket0.computes:
    path = f'C:\\Temp\\{compute.name}_dump.csv'
    dpm.fuse_dump(base=compute.fuses, file_path=path)
    print(f"Dumped {compute.name}")
```

### Output Format

CSV file with columns:
- `Register Name` - Full register path
- `Current Value` - Hex value from hardware
- `Default Value` - Design default
- `Address` - RAM/PRAM address
- `Bit Width` - Register width
- `Category` - Register classification
- `Group` - Functional group

---

## Common Workflows

### Workflow 1: Debug Memory Hangs

```python
import S2T.dpmChecks as dpm

# Reproduce hang condition
# ... run test until hang ...

# Capture TOR state during hang
dpm.tor_dump(
    destination_path='C:\\Debug\\MemoryHang',
    visual_id='hang_condition_001'
)

# Analyze Excel file for stuck transactions
```

### Workflow 2: Compare Two Units

```python
import S2T.dpmChecks as dpm
import pandas as pd

# Dump Unit 1 (known good)
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\unit1_baseline.csv'
)

# Switch to Unit 2 (failing)
# ...

# Dump Unit 2
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\unit2_failing.csv'
)

# Compare using pandas
unit1 = pd.read_csv('C:\\Temp\\unit1_baseline.csv')
unit2 = pd.read_csv('C:\\Temp\\unit2_failing.csv')

merged = unit1.merge(unit2, on='Register Name', suffixes=('_1', '_2'))
diff = merged[merged['Current Value_1'] != merged['Current Value_2']]

print(f"Found {len(diff)} differences")
diff.to_csv('C:\\Temp\\differences.csv', index=False)
```

### Workflow 3: Create Custom Fuse File from Dump

```python
import S2T.dpmChecks as dpm
import pandas as pd

# Step 1: Dump current configuration
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\current.csv'
)

# Step 2: Load and filter
df = pd.read_csv('C:\\Temp\\current.csv')
target_regs = df[df['Register Name'].str.contains('fivr|freq')]

# Step 3: Create .fuse file
with open('C:\\Temp\\custom.fuse', 'w') as f:
    f.write('# Custom configuration\n\n')
    f.write('[sv.socket0.cbb0.base.fuses]\n')
    for idx, row in target_regs.iterrows():
        reg = row['Register Name'].split('.')[-1]
        val = row['Current Value']
        f.write(f'{reg} = {val}\n')

# Step 4: Use the fuse file
fuses = dpm.process_fuse_file('C:\\Temp\\custom.fuse')
config = dpm.external_fuses(external_fuses=fuses, bsformat=True)
dpm.pseudo_bs(ClassMask='FirstPass', fuse_cbb=config, boot=True)
```

### Workflow 4: Baseline Documentation

```python
import S2T.dpmChecks as dpm
from datetime import datetime

# Create timestamped baseline
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
visual = dpm.visual_str()

# Dump all critical dies
for cbb in sv.socket0.cbbs:
    filename = f'baseline_{visual}_{cbb.name}_{timestamp}.csv'
    path = f'C:\\Baselines\\{filename}'
    dpm.fuse_dump(base=cbb.base.fuses, file_path=path)
    print(f"Saved baseline: {filename}")
```

---

## Command Reference

### MDT Tools

```python
import S2T.dpmChecks as dpm

# TOR dump
dpm.tor_dump(destination_path=None, visual_id=None)

# Initialize MDT tools
mdt = dpm.mdt_tools()

# Check components
mdt.print_available_components()
mdt.get_available_components()  # Returns dict
```

### Fuse Dumps

```python
import S2T.dpmChecks as dpm

# Create dump
dpm.fuse_dump(base, file_path)

# Refresh fuses before dump (if needed)
dpm.fuseRAM(refresh=True)
```

### Parameters

**`tor_dump()`**
- `destination_path` (str, optional) - Output directory (default: `C:\Temp`)
- `visual_id` (str, optional) - Identifier for filename (default: timestamp)

**`fuse_dump()`**
- `base` (PythonSV object, required) - Register base to dump
- `file_path` (str, required) - Output CSV file path

---

## File Locations

### Output Files

| Type | Default Location | Format |
|------|------------------|--------|
| TOR dumps | `C:\Temp\tor_dump_*.xlsx` | Excel (multi-sheet) |
| Fuse dumps | User-specified | CSV |
| Dump logs | `C:\Temp\RegisterDumpLogs\*.log` | Text |

### Example Naming

```
# TOR dumps
tor_dump_<visual_id>_<timestamp>.xlsx
tor_dump_2026-02-16_14-30-45.xlsx
tor_dump_GNRAP_U0042_test1_2026-02-16_14-30-45.xlsx

# Fuse dumps
<custom_name>.csv
cbb0_baseline.csv
GNRAP_U0042_compute0_20260216.csv
```

---

## Best Practices

### 1. Naming Conventions

```python
# Include unit ID and test info
visual_id = f"{dpm.product_str()}_{dpm.visual_str()}_{test_name}"

# Timestamped baselines
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"baseline_{visual_id}_{timestamp}.csv"
```

### 2. Organize Output

```python
# Create organized directory structure
import os

debug_dir = f'C:\\Debug\\{dpm.visual_str()}'
os.makedirs(debug_dir, exist_ok=True)

# Save all outputs to unit-specific folder
dpm.tor_dump(destination_path=debug_dir, visual_id='mesh_test1')
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path=f'{debug_dir}\\cbb0_dump.csv'
)
```

### 3. Version Control Baselines

```bash
# Store baseline dumps in Git
mkdir C:\Git\Automation\Baselines
cd C:\Git\Automation\Baselines
git add *.csv
git commit -m "Add baseline for GNRAP U0042"
git push
```

### 4. Regular Backups

```python
# Automated baseline capture
def capture_baseline(unit_id, test_name):
    import S2T.dpmChecks as dpm
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = f'C:\\Baselines\\{unit_id}\\{test_name}'
    os.makedirs(base_dir, exist_ok=True)

    # Dump all dies
    for cbb in sv.socket0.cbbs:
        path = f'{base_dir}\\{cbb.name}_{timestamp}.csv'
        dpm.fuse_dump(base=cbb.base.fuses, file_path=path)

    print(f"Baseline captured: {base_dir}")

# Usage
capture_baseline('GNRAP_U0042', 'mesh_sweep')
```

---

## Troubleshooting

### Issue: TOR dump fails with "CCF not available"

**Solution:**
```python
# Verify debug module is available
try:
    import debug
    print("Debug module loaded")
except:
    print("ERROR: debug module not available")
    print("Ensure you're in PythonSV environment")
```

### Issue: Fuse dump creates empty file

**Solution:**
```python
# Force fuse refresh
dpm.fuseRAM(refresh=True)
import time
time.sleep(2)  # Wait for refresh
dpm.fuse_dump(base=sv.socket0.cbb0.base.fuses, file_path='C:\\Temp\\test.csv')
```

### Issue: Permission denied writing file

**Solution:**
- Ensure output directory exists
- Close Excel if file is open
- Check write permissions
- Use different filename

### Issue: Some registers show 0x0

**Solution:**
- Boot unit to EFI or OS first
- Some registers only valid in specific power states
- Verify IPC connection: `ipc.unlock()`

---

## Integration with Existing Workflows

### With Logger

```python
import S2T.dpmChecks as dpm

# Run test with logger
dpm.logger(
    visual='U0042',
    TestName='mesh_sweep',
    Testnumber=1,
    dr_dump=True
)

# Capture additional debug data
dpm.tor_dump(visual_id='U0042_mesh_sweep_T1')
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\U0042_mesh_sweep_T1_fuses.csv'
)
```

### With Pseudo Bootscript

```python
import S2T.dpmChecks as dpm

# Capture baseline before boot
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\before_boot.csv'
)

# Run pseudo bootscript
dpm.pseudo_bs(ClassMask='FirstPass', boot=True)

# Capture after boot
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\after_boot.csv'
)

# Compare to verify fuse application
```

### With Quick Test GUIs

```python
import S2T.SetTesterRegs as s2t
import S2T.dpmChecks as dpm

# Run quick test
s2t.MeshQuickTest(GUI=True)

# If test fails, capture debug data
if test_failed:
    dpm.tor_dump(visual_id='mesh_test_failure')
    for cbb in sv.socket0.cbbs:
        path = f'C:\\Debug\\{cbb.name}_failure.csv'
        dpm.fuse_dump(base=cbb.base.fuses, file_path=path)
```

---

## Generating Fuse Files from Register Arrays

### Overview

The `FuseFileGenerator` class performs the **inverse operation** of reading fuse files - it creates external `.fuse` files from register arrays. This is useful when you have register configurations from register dumps, test scripts, or programmatic configurations that need to be formatted as reusable fuse files.

**Supported Products:** GNR, DMR, CWF, and extensible to future products

### Quick Start

```python
from S2T.Tools.registerdump import FuseFileGenerator
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen

# Your register array (from register dump, calculations, etc.)
register_array = [
    'sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa',
    'sv.socket0.compute1.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point0= 0xaa',
    'sv.socket0.compute0.fuses.pcu.pcode_ddrd_ddr_vf_voltage_point1= 0xb1',
]

# Generate fuse file
generator = FuseFileGenerator(gnr_fusefilegen, register_array, product='gnr')
generator.create_fuse_file()
# Output: C:\Temp\RegisterDumpLogs\2026-02-17_143022_generated.fuse
```

### Product-Specific Usage

#### GNR/CWF Example

```python
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen

gnr_registers = [
    'sv.socket0.compute0.fuses.pcu.config_register1= 0x10',
    'sv.socket0.io0.fuses.pcie.link_config= 0xB2',
    'sv.sockets.computes.fuses.pcu.global_setting= 0xFF',  # Applies to all
]

generator = FuseFileGenerator(gnr_fusefilegen, gnr_registers, product='gnr')
generator.create_fuse_file()
```

#### DMR Example

```python
from S2T.product_specific.dmr import fusefilegen as dmr_fusefilegen

dmr_registers = [
    'sv.socket0.cbb0.base.fuses.pcu.config_register1= 0x10',
    'sv.socket0.cbb0.compute0.fuses.pcu.compute_config= 0x20',
    'sv.socket0.imh0.fuses.memory.timing_register= 0x30',
    'sv.sockets.cbbs.base.fuses.pcu.global_setting= 0xFF',  # All CBBs
]

generator = FuseFileGenerator(dmr_fusefilegen, dmr_registers, product='dmr')
generator.create_fuse_file()
```

### Custom Output Path

```python
# Specify custom output location
output_path = r"C:\MyProject\configs\custom_fuses.fuse"
generator = FuseFileGenerator(
    gnr_fusefilegen,
    register_array,
    product='gnr',
    output_file=output_path
)
generator.create_fuse_file()
```

### Generated Fuse File Format

The output is in the standard `.fuse` format compatible with external fuse file processing:

```ini
# Fuse file generated from register array
# Generated on: 2026-02-17 14:30:22
# Total sections: 2
# Total registers: 3

[sv.socket0.compute0.fuses]
pcu.config_register1 = 0x10
pcu.pcode_ddrd_ddr_vf_voltage_point0 = 0xaa
pcu.pcode_ddrd_ddr_vf_voltage_point1 = 0xb1

[sv.socket0.compute1.fuses]
pcu.pcode_ddrd_ddr_vf_voltage_point0 = 0xaa
```

### Get Generation Report

```python
generator = FuseFileGenerator(gnr_fusefilegen, register_array, product='gnr')
generator.create_fuse_file()

# Get detailed report
report = generator.get_report()
print(f"Product: {generator.product.upper()}")
print(f"Output file: {report['output_file']}")
print(f"Sections: {report['section_count']}")
print(f"Registers: {report['register_count']}")
print(f"Errors: {len(report['errors'])}")
print(f"Warnings: {len(report['warnings'])}")
```

### Supported Hierarchies

#### GNR/CWF
- `sv.socket<N>.compute<N>.fuses` - Specific socket and compute
- `sv.socket<N>.io<N>.fuses` - Specific socket and IO
- `sv.sockets.computes.fuses` - All sockets, all computes
- `sv.sockets.ios.fuses` - All sockets, all IOs

#### DMR
- `sv.socket<N>.cbb<N>.base.fuses` - Specific socket, CBB base
- `sv.socket<N>.cbb<N>.compute<N>.fuses` - Specific socket, CBB, compute
- `sv.socket<N>.imh<N>.fuses` - Specific socket and IMH
- `sv.sockets.cbbs.base.fuses` - All sockets, all CBBs base
- `sv.sockets.cbbs.computes.fuses` - All sockets, CBBs, computes
- `sv.sockets.imhs.fuses` - All sockets, all IMHs

### Common Workflows

#### Workflow 1: Convert Register Dump to Reusable Fuse File

```python
import S2T.dpmChecks as dpm
from S2T.Tools.registerdump import FuseFileGenerator
from S2T.product_specific.dmr import fusefilegen as dmr_fusefilegen

# Step 1: Get register dump (existing functionality)
# This creates a raw register list
dpm.fuse_dump(
    base=sv.socket0.cbb0.base.fuses,
    file_path='C:\\Temp\\cbb0_dump.csv'
)

# Step 2: Extract specific registers you want to preserve
important_registers = [
    'sv.socket0.cbb0.base.fuses.pcu.voltage_config= 0xAB',
    'sv.socket0.cbb0.base.fuses.pcu.frequency_setting= 0x12',
    'sv.socket0.cbb0.base.fuses.memory.timing_param= 0xFF',
]

# Step 3: Generate reusable fuse file
generator = FuseFileGenerator(
    dmr_fusefilegen,
    important_registers,
    product='dmr',
    output_file='C:\\Configs\\working_config.fuse'
)
generator.create_fuse_file()

# Step 4: Now you can use this file in future tests
# See FUSE_FILE_QUICK_REFERENCE.md for usage
```

#### Workflow 2: Create Test Configuration from Script

```python
from S2T.Tools.registerdump import FuseFileGenerator
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen

# Programmatically build register configuration
voltage_points = []
for socket in range(3):
    for voltage_level in range(4):
        value = 0xaa + voltage_level * 0x10
        register = (
            f'sv.socket0.compute{socket}.fuses.pcu.'
            f'pcode_ddrd_ddr_vf_voltage_point{voltage_level}= {hex(value)}'
        )
        voltage_points.append(register)

# Generate fuse file for these settings
generator = FuseFileGenerator(
    gnr_fusefilegen,
    voltage_points,
    product='gnr',
    output_file='C:\\TestConfigs\\voltage_sweep_test.fuse'
)
generator.create_fuse_file()

# Use in your test
import S2T.dpmChecks as dpm
fuses = dpm.process_fuse_file('C:\\TestConfigs\\voltage_sweep_test.fuse')
config = dpm.external_fuses(external_fuses=fuses, bsformat=True)
dpm.pseudo_bs(ClassMask='RowEvenPass', fuse_cbb=config, boot=True)
```

#### Workflow 3: Replicate Golden Configuration Across Units

```python
from S2T.Tools.registerdump import FuseFileGenerator
from S2T.product_specific.dmr import fusefilegen as dmr_fusefilegen

# Extract golden configuration from one unit
golden_config = [
    'sv.socket0.cbb0.base.fuses.pcu.golden_setting1= 0x100',
    'sv.socket0.cbb0.base.fuses.pcu.golden_setting2= 0x200',
]

# Replicate to all CBBs using plural sections
replicated_config = [
    'sv.sockets.cbbs.base.fuses.pcu.golden_setting1= 0x100',
    'sv.sockets.cbbs.base.fuses.pcu.golden_setting2= 0x200',
]

generator = FuseFileGenerator(
    dmr_fusefilegen,
    replicated_config,
    product='dmr',
    output_file='C:\\Configs\\replicated_golden.fuse'
)
generator.create_fuse_file()
```

### Features

- **Multi-Product Support** - Works with GNR, DMR, CWF automatically
- **Automatic Parsing** - Extracts sections and register names from full paths
- **Validation** - Validates against product-specific hierarchy patterns
- **Duplicate Detection** - Warns about duplicate registers
- **Sorted Output** - Sections and registers alphabetically sorted
- **Timestamped Files** - Auto-generated filenames with timestamps
- **Custom Paths** - Specify exact output location
- **Error Reporting** - Detailed error and warning messages

### Verification Workflow

After generating a fuse file, verify it works correctly:

```python
import S2T.dpmChecks as dpm
from S2T.product_specific.gnr import fusefilegen as gnr_fusefilegen
from S2T.product_specific.gnr.fusefilegen import process_fuse_file

# Generate fuse file
generator = FuseFileGenerator(gnr_fusefilegen, register_array, product='gnr')
generator.create_fuse_file()

# Verify by reading it back
registers = process_fuse_file(generator.fuse_file_path)
print(f"Successfully parsed {len(registers)} registers")

# Use in test to confirm functionality
config = dpm.external_fuses(external_fuses=registers, bsformat=True)
dpm.pseudo_bs(ClassMask='FirstPass', fuse_cbb=config, boot=True)
```

### Error Handling

```python
generator = FuseFileGenerator(gnr_fusefilegen, invalid_array, product='gnr')

if not generator.create_fuse_file():
    # Check errors
    for error in generator.errors:
        print(f"ERROR: {error}")
    
    # Check warnings
    for warning in generator.warnings:
        print(f"WARNING: {warning}")
else:
    print(f"Successfully generated: {generator.fuse_file_path}")
```

### File Locations

**Default Output Directory:**
- `C:\Temp\RegisterDumpLogs\`

**Auto-generated Filename Format:**
- `YYYY-MM-DD_HHMMSS_generated.fuse`
- Example: `2026-02-17_143022_generated.fuse`

**Related Files:**
- Example script: `S2T\BASELINE\S2T\Tools\fusefile_generator_example.py`
- Class implementation: `S2T\BASELINE\S2T\Tools\registerdump.py`
- Product patterns: `S2T\BASELINE\S2T\product_specific\{gnr|dmr|cwf}\fusefilegen.py`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | February 17, 2026 | Added FuseFileGenerator documentation and workflows |
| 1.0 | February 16, 2026 | Initial MDT tools and fuse dump documentation |

---

## Related Documentation

- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Complete installation instructions
- **[THR_DEBUG_FRAMEWORK_USER_MANUAL.md](THR_DEBUG_FRAMEWORK_USER_MANUAL.md)** - Full framework documentation
- **[FUSE_FILE_QUICK_REFERENCE.md](FUSE_FILE_QUICK_REFERENCE.md)** - External fuse file format guide

---

**For Support:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

**© 2026 Intel Corporation. Intel Confidential.**
