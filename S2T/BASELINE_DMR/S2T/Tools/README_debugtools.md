# MDT_Tools Class - Debug Components Wrapper

## Overview
The `MDT_Tools` class provides a convenient wrapper for accessing all debug.mdt_tools components with dynamic initialization.

## Features

### ✅ Dynamic Component Initialization
All 41 debug components are automatically initialized as instance attributes:
- `self.asf`, `self.cache`, `self.cms`, `self.ccf`, `self.cpm`, `self.cxlcm`
- `self.dda`, `self.dsa`, `self.fivr`, `self.hamvf`, `self.hap`, `self.hiop`
- `self.hwrs`, `self.iaa`, `self.iommu`, `self.iosfsb2ucie`, `self.iosf2sfi`
- `self.isa`, `self.lcpll`, `self.ljpll`, `self.mc_subch`, `self.mse`
- `self.oobmsm`, `self.pcie`, `self.punit`, `self.rasip`, `self.resctrl`
- `self.rsrc_adapt`, `self.dts`, `self.rstw`, `self.s3m`, `self.sca`
- `self.ubox`, `self.ubr`, `self.uciephy`, `self.ula`, `self.cxl`, `self.fsa`

### ✅ Availability Checking
Components that aren't available in `debug.mdt_tools` are set to `None` with a warning message.

## Usage

### Basic Initialization
```python
import debug
from Tools.debugtools import MDT_Tools

# Initialize the wrapper
mdt = MDT_Tools(debug)
```

### Accessing Debug Components
```python
# Use any component directly
if mdt.ccf:
    tor_data = mdt.ccf.get_cbos_tor_dump()
    tor_valid = mdt.ccf.get_cbos_tor_trk_valid()

if mdt.cache:
    cache_data = mdt.cache.some_method()

if mdt.asf:
    asf_info = mdt.asf.get_status()
```

### Built-in Helper Methods

#### 1. Check Available Components
```python
# Print formatted list of all components
mdt.print_available_components()

# Get dictionary of component availability
status = mdt.get_available_components()
# Returns: {'asf': True, 'cache': True, 'ccf': True, ...}
```

#### 2. TOR Dump to Excel
```python
# Generate TOR dump and save to Excel
mdt.dpm_tor_dump(
    destination_path=r"C:\Temp",
    visual_id="experiment_001"
)
# Creates: C:\Temp\20260212_143022_experiment_001_Tordump.xlsx
```

#### 3. Save Tracker Data to Excel
```python
# Save multiple trackers to one Excel file (multiple sheets)
trackers = [tracker1, tracker2, tracker3]
mdt.dpm_save_excel_data(
    trackers,
    destination_path=r"C:\Results",
    visual_id="test_run"
)
```

#### 4. Multi-Component Check
```python
# Check multiple components at once
results = mdt.custom_multi_component_check(['ccf', 'cache', 'asf'])
# Returns detailed info about each component
```

## Custom Functions (Expandable)

The class includes placeholder custom functions that can be expanded on demand:

### Custom CCF Decoder
```python
def custom_ccf_decode(self, value, decode_type='opcode'):
    # Add your custom CCF decoding logic here
    pass
```

### Custom Cache Analysis
```python
def custom_cache_analysis(self, **kwargs):
    # Add your custom cache analysis logic here
    pass
```

## Example Output

### Initialization Output
```
Initialized asf
Initialized cache
Initialized cms
Initialized ccf
Initialized cpm
Initialized cxlcm
...
Initialized cxl
Initialized fsa
```

### Component Status Output
```
============================================================
DEBUG COMPONENTS STATUS
============================================================

Available (41):
  ✓ asf
  ✓ cache
  ✓ cms
  ✓ ccf
  ✓ cpm
  ...
  ✓ cxl
  ✓ fsa

============================================================
```

## Architecture

### Class Structure
```
MDT_Tools
├── DEBUG_COMPONENTS (list of all 41 component names)
├── __init__() - Initialize with debug module
├── _initialize_debug_components() - Dynamic component setup
│
├── dpm_tor_dump() - TOR dump to Excel
├── dpm_save_excel_data() - Generic tracker to Excel
│
├── get_available_components() - Get availability dict
├── print_available_components() - Print formatted status
│
└── Custom Functions (expandable on demand)
    ├── custom_ccf_decode()
    ├── custom_cache_analysis()
    └── custom_multi_component_check()
```

## Adding New Custom Functions

To add new custom functions:

1. Add the method to the class
2. Use component availability checks:
   ```python
   def my_custom_function(self):
       if not self.ccf:
           print("Error: CCF not available")
           return

       # Your custom logic here
       result = self.ccf.some_method()
       return result
   ```

## Notes

- All component methods from `debug.mdt_tools` are directly accessible
- Components check for `None` before use is recommended
- The class mirrors all functionality from the original debug module
- Initialization prints show which components were successfully loaded
- Components set to `None` if not available in the environment

## Integration

This class is designed to work seamlessly with existing S2T and DebugFramework workflows:
- Compatible with all DMR debug utilities
- Can be used in automation scripts
- Supports all standard debug component operations
- Ready for custom decoding and analysis functions
