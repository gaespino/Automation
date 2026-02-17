# Fuse File Generator - Engineering Tools

## Overview

The **Fuse File Generator** is a comprehensive engineering tool for managing, filtering, and generating fuse configuration files. It processes raw CSV fuse data from product-specific folders and generates `.fuse` files compatible with the `fusefilegen.py` tool used in S2T workflows.

This tool is part of the **PPV Engineering Tools** suite and features a distinctive orange color scheme.

---

## Features

### Data Management
- **Multi-File Loading**: Automatically loads and combines all CSV files from product-specific fuse folders
- **IP Origin Tracking**: Each fuse is tagged with its IP origin (Compute, IO, CBB, IMH) based on the source CSV filename
- **Column Selection**: Choose which columns to display from the available data
- **Advanced Filtering**: Filter data by any column with support for wildcards
- **Search Functionality**: Search fuses by description, instance name, or any other field

### Interactive Table View
- **Sortable Columns**: Click column headers to sort data
- **Selection Tools**:
  - Select All
  - Clear All
  - Select Filtered (select only currently filtered fuses)
  - Clear Filtered (deselect only currently filtered fuses)
- **Real-time Selection Count**: Always see how many fuses are selected

### Product-Specific Configuration
- **Multi-Product Support**: GNR, CWF, and DMR with product-specific hierarchy patterns
- **IP Instance Configuration**: Configure individual IP instances or apply values to all (plural registers)

#### GNR / CWF Configuration
- **Computes**: compute0, compute1, compute2 (or all_computes)
- **IOs**: io0, io1 (or all_ios)

#### DMR Configuration
- **CBBs Base**: cbb0-3 with base.fuses hierarchy
- **CBBs Top**: cbb0-3 with compute0-3 split (compute.fuses hierarchy)
- **IMHs**: imh0-1 (or all_imhs)

### Fuse File Generation
- **Product-Aware**: Generates files with correct hierarchy patterns for the selected product
- **Multiple Output Formats**: Compatible with fusefilegen.py parser
- **Validation**: Validates hex values before file generation
- **Batch Configuration**: Configure multiple IP instances with different values in a single session

---

## File Structure

```
PPV/
├── utils/
│   └── fusefilegenerator.py      # Backend processor and generator
├── gui/
│   └── fusefileui.py              # Interactive UI
└── configs/
    └── fuses/
        ├── gnr/
        │   ├── compute.csv        # GNR compute fuses
        │   └── io.csv             # GNR IO fuses
        ├── cwf/
        │   ├── compute.csv        # CWF compute fuses
        │   └── io.csv             # CWF IO fuses
        └── dmr/
            ├── cbb.csv            # DMR CBB fuses
            └── imh.csv            # DMR IMH fuses
```

---

## Usage

### Launching the Tool

#### From PPV Tools Hub
1. Open PPV Tools Hub
2. Locate the **Fuse File Generator** card (orange/engineering theme)
3. Click "Launch Tool →"

#### Standalone Execution
```bash
cd PPV/gui
python fusefileui.py
```

#### Programmatic Usage
```python
from PPV.gui.fusefileui import FuseFileUI
import tkinter as tk

root = tk.Tk()
app = FuseFileUI(root, default_product='GNR')
root.mainloop()
```

---

## Workflow

### Step 1: Load Product Data
1. Select your product (GNR, CWF, or DMR) from the header radio buttons
2. Data automatically loads from `configs/fuses/<product>/`
3. A statistics popup shows total fuses loaded and IP origins

### Step 2: Select Display Columns
1. In the "Display Columns" listbox, select columns you want to view
   - Default columns: Instance, original_name, description, IP_Origin, default, FUSE_WIDTH
2. Click **"📋 Show Data"** to display the table

### Step 3: Filter and Search
1. **Search**: Enter search terms in the search box and press Enter or click "Search"
   - Searches across displayed columns
2. **Filter**: Use column-specific filters (if implemented in full version)
3. **Clear Search**: Reset to show all data

### Step 4: Select Fuses
Use selection tools to choose fuses:
- **Select All**: Select all visible fuses
- **Clear All**: Deselect everything
- **Select Filtered**: Select only currently filtered fuses
- **Clear Filtered**: Deselect only currently filtered fuses

### Step 5: Start Fuse Generation
1. Click **"▶ Start Fuse Generation"** (requires at least one selected fuse)
2. Configuration window opens with product-specific IP options

### Step 6: Configure IP Instances
For each IP type:
1. **Individual Values**: Enter hex values (e.g., `0x1`, `0xFF`) for each instance
2. **Apply to All**: Enter a value and click "Apply Value to All" to use plural registers

### Step 7: Generate File
1. Click **"✓ Generate Fuse File"**
2. Choose output location
3. File is generated with proper hierarchy format for the selected product

---

## CSV File Format

The tool expects CSV files with the following common columns:
- **original_name**: Fuse register name
- **Instance**: Instance identifier
- **description**: Fuse description
- **IP_Origin**: (Auto-added) IP type from filename
- **default**: Default value
- **FUSE_WIDTH**: Width in bits
- Additional product-specific columns

### Example CSV Structure
```csv
original_name,Instance,description,default,FUSE_WIDTH
bgr_c01/bgr_trim_en,bgr_cbb_trim_cntrl_cfg2_bgr_trim_en,Trim enable bit,0,1
bgr_c01/bgr_offset,bgr_cbb_trim_cntrl_cfg0_bgr_offset,Offset code,128,8
```

---

## Generated .fuse File Format

### GNR Example
```ini
# Fuse configuration file for GNR
# Generated by PPV Engineering Tools - Fuse File Generator

[sv.socket0.compute0.fuses]
registerx1 = 0x1
registerx2 = 0x2

[sv.sockets.computes.fuses]
common_reg = 0xFF
```

### DMR Example
```ini
# Fuse configuration file for DMR
# Generated by PPV Engineering Tools - Fuse File Generator

[sv.socket0.cbb0.base.fuses]
register1 = 0x1

[sv.socket0.cbb0.compute0.fuses]
compute_reg = 0x10

[sv.sockets.cbbs.base.fuses]
shared_reg = 0xFF
```

---

## Backend API

### FuseFileGenerator Class

```python
from PPV.utils.fusefilegenerator import FuseFileGenerator, load_product_fuses

# Load fuses for a product
generator = load_product_fuses('GNR')

# Get statistics
stats = generator.get_statistics()
print(f"Total fuses: {stats['total_fuses']}")

# Search fuses
results = generator.search_fuses('bgr', ['description', 'original_name'])

# Filter fuses
filtered = generator.filter_fuses({
    'IP_Origin': 'COMPUTE',
    'FUSE_WIDTH': '1'
})

# Generate fuse file
ip_assignments = {
    'compute0': {'register1': '0x1', 'register2': '0xFF'},
    'all_computes': {'common_reg': '0xAB'}
}
generator.generate_fuse_file(selected_fuses, ip_assignments, 'output.fuse')

# Export to CSV
generator.export_to_csv(filtered, 'export.csv', columns=['original_name', 'description'])
```

---

## Product Hierarchy Patterns

### GNR / CWF
```
Specific:
- sv.socket<N>.compute<N>.fuses
- sv.socket<N>.io<N>.fuses

Plural (All):
- sv.sockets.computes.fuses
- sv.sockets.ios.fuses
```

### DMR
```
Specific:
- sv.socket<N>.cbb<N>.base.fuses
- sv.socket<N>.cbb<N>.compute<N>.fuses
- sv.socket<N>.imh<N>.fuses

Plural (All):
- sv.sockets.cbbs.base.fuses
- sv.sockets.cbbs.computes.fuses
- sv.sockets.imhs.fuses
```

---

## Tips and Best Practices

### Column Selection
- Start with default columns (Instance, original_name, description)
- Add product-specific columns as needed for filtering
- Use IP_Origin column to filter by IP type

### Filtering
- Use wildcards: `*value*` (contains), `value*` (starts with), `*value` (ends with)
- Combine multiple filters for precise selection
- Use "Select Filtered" to work with filtered subset

### Value Configuration
- Always use hex format: `0x1`, `0xFF`, `0xDEADBEEF`
- Use "Apply to All" for uniform configuration across IPs
- Mix individual and plural configurations as needed

### File Organization
- Keep CSV files organized by product in `configs/fuses/<product>/`
- Name CSV files by IP type: compute.csv, io.csv, cbb.csv, imh.csv
- One IP type per CSV file for clear origin tracking

---

## Integration with S2T

Generated `.fuse` files are compatible with S2T's fusefilegen.py tools:

```bash
# GNR
cd S2T/product_specific/gnr
python fusefilegen.py generated_fuses.fuse

# DMR
cd S2T/product_specific/dmr
python fusefilegen.py generated_fuses.fuse
```

The generated arrays can be passed directly to CoreManipulation for register programming.

---

## Color Scheme - Engineering Tools

The Fuse File Generator uses a distinctive **orange theme** to identify it as part of the Engineering Tools group:

- **Primary**: `#e67e22` (Orange)
- **Dark**: `#d35400` (Dark Orange)
- **Light**: `#f39c12` (Light Orange/Gold)

This distinguishes it from other tool categories in the PPV Tools Hub:
- Debug Tools: Blue/Red/Purple
- Framework Tools: Green/Teal
- Engineering Tools: Orange (New)

---

## Troubleshooting

### "No CSV files found"
- Verify CSV files exist in `PPV/configs/fuses/<product>/`
- Check product name is lowercase in folder path
- Ensure CSV files have `.csv` extension

### "Invalid hex value"
- Values must start with `0x`
- Use uppercase or lowercase hex digits: `0xFF` or `0xff`
- No spaces or special characters

### "Failed to generate fuse file"
- Check write permissions for output directory
- Verify at least one fuse is selected
- Ensure IP assignments are configured

### Column selection not showing data
- Click "Show Data" button after selecting columns
- Ensure at least one column is selected
- Verify data was loaded successfully

---

## Future Enhancements

Potential future features:
- Column-level filters in table headers
- Import/export filter configurations
- Batch processing multiple fuse sets
- History of generated configurations
- Template management for common configurations
- Integration with Debug Framework Control Panel

---

## Support

For issues, feature requests, or questions:
- Engineering Tools Team
- PPV Debug Tools Suite
- THR Debug Tools Hub

---

## Related Documentation

- [S2T FUSEFILEGEN_README.md](../../S2T/BASELINE_DMR/S2T/product_specific/FUSEFILEGEN_README.md) - fusefilegen.py documentation
- [PPV Tools Hub](PPVTools.py) - Main tools launcher
- [Product-Specific Hierarchies](../../S2T/BASELINE_DMR/S2T/product_specific/) - GNR, CWF, DMR fusefilegen implementations

---

**Version**: 1.0
**Date**: February 2026
**Author**: Engineering Tools Team
**Category**: Engineering Tools - Fuse Management
