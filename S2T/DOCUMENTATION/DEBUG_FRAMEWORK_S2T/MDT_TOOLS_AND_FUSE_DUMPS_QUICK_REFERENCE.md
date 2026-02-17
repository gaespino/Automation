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

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | February 16, 2026 | Initial MDT tools and fuse dump documentation |

---

## Related Documentation

- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** - Complete installation instructions
- **[THR_DEBUG_FRAMEWORK_USER_MANUAL.md](THR_DEBUG_FRAMEWORK_USER_MANUAL.md)** - Full framework documentation
- **[FUSE_FILE_QUICK_REFERENCE.md](FUSE_FILE_QUICK_REFERENCE.md)** - External fuse file format guide

---

**For Support:** Gabriel Espinoza (gabriel.espinoza.ballestero@intel.com)

**© 2026 Intel Corporation. Intel Confidential.**
