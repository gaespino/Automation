# Fuse File Generator - Quick Start Guide

## 5-Minute Quick Start

### 1. Launch the Tool
From PPV Tools Hub → Click **"Fuse File Generator"** (orange card)

### 2. Select Product
Choose GNR, CWF, or DMR from the header

### 3. Choose Columns & Show Data
1. Select columns from the listbox:
   - `Instance`
   - `original_name`
   - `description`
   - `IP_Origin`
2. Click **"📋 Show Data"**

### 4. Search & Filter
- Enter search term: e.g., "bgr" or "trim"
- Click **Search** or press Enter

### 5. Select Fuses
- Click **"Select Filtered"** to select visible fuses
- Or manually click rows to select

### 6. Generate Configuration
1. Click **"▶ Start Fuse Generation"**
2. Enter values for IP instances (e.g., `0x1`, `0xFF`)
3. Or use **"Apply to All"** for uniform values
4. Click **"✓ Generate Fuse File"**
5. Save your `.fuse` file

**Done!** Your fuse configuration file is ready for fusefilegen.py

---

## Common Use Cases

### Use Case 1: Configure All Computes with Same Value
```
1. Search for desired fuses
2. Select filtered fuses
3. In generation window:
   - Computes → Apply to All: 0xFF
   - Click "Apply Value to All"
4. Generate file
```

### Use Case 2: Different Values Per IP
```
1. Select fuses
2. In generation window:
   - compute0: 0x1
   - compute1: 0x2
   - compute2: 0x3
3. Generate file
```

### Use Case 3: DMR CBB Configuration
```
1. Select CBB-related fuses
2. In generation window:
   - CBBs Base → cbb0: 0x10
   - CBBs Base → cbb1: 0x20
   - CBBs Top → cbb0_compute0: 0xAB
4. Generate file
```

---

## Keyboard Shortcuts

- **Enter** in search box: Apply search
- **Escape**: Clear search (when focused)
- **Ctrl+A** in tree: Select all visible (when focused)

---

## Quick Tips

✓ Always use hex format: `0x1`, `0xFF`, `0xDEADBEEF`
✓ Search before selecting for targeted fuse selection
✓ Use "Select Filtered" to work with search results
✓ "Apply to All" uses plural registers (all IPs at once)
✓ Export to CSV for offline analysis or sharing

---

## File Locations

**Input CSV Files**:
```
PPV/configs/fuses/gnr/compute.csv
PPV/configs/fuses/gnr/io.csv
PPV/configs/fuses/dmr/cbb.csv
PPV/configs/fuses/dmr/imh.csv
```

**Output .fuse Files**:
Save anywhere, typically:
```
S2T/product_specific/gnr/my_config.fuse
S2T/product_specific/dmr/my_config.fuse
```

---

## Example Workflow: GNR BGR Fuses

```
1. Launch Tool → Select GNR
2. Select Columns: Instance, original_name, description
3. Show Data
4. Search: "bgr"
5. Select Filtered (selects all BGR fuses)
6. Start Fuse Generation
7. Computes → Apply to All: 0x1
8. Generate: save as "gnr_bgr_config.fuse"
9. Use with fusefilegen.py:
   cd S2T/product_specific/gnr
   python fusefilegen.py gnr_bgr_config.fuse
```

---

## Need Help?

- Full documentation: [FUSE_GENERATOR_README.md](FUSE_GENERATOR_README.md)
- S2T Integration: [FUSEFILEGEN_README.md](../../S2T/BASELINE_DMR/S2T/product_specific/FUSEFILEGEN_README.md)
- PPV Tools: Launch "THR Debug Tools Hub"

---

**Quick Reference Card**

| Action | How |
|--------|-----|
| Load data | Select product (auto-loads) |
| Show table | Select columns → Show Data |
| Search | Enter term → Search button |
| Select all | Select All button |
| Select visible | Select Filtered button |
| Generate | Start Fuse Generation button |
| Export | Export to CSV button |

---

*Part of PPV Engineering Tools Suite - Orange Theme*
