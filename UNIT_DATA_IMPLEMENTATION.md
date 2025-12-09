# Unit Data Configuration - Implementation Summary

## Overview
Unit Data fields are now properly configured as a separate section that applies to ALL experiments. These fields are rendered in the left panel and are NOT displayed in individual experiment forms.

## What Changed

### 1. Configuration Structure
Created a new **"Unit Data"** section containing 5 fields:
- **Product** (str) - Product type: GNR, CWF, or DMR
- **Visual ID** (str) - Unit Visual ID
- **Bucket** (str) - Unit Assigned Bucket
- **COM Port** (int) - Serial Port to communicate to MB
- **IP Address** (str) - IP Address to communicate to MB

### 2. Field Migration
Moved Unit Data fields from their previous locations:
- `Visual ID` and `Bucket`: Moved from "Basic Information" → "Unit Data"
- `COM Port` and `IP Address`: Moved from "Advanced Configuration" → "Unit Data"
- `Product`: Added as new field in "Unit Data"

### 3. Code Changes

#### ExperimentBuilder.py Updates:

**a) Default Template (get_default_template):**
- Updated to define Unit Data fields in their own section
- Added Product field with options: ["GNR", "CWF", "DMR"]

**b) Unit Data Field Creation (create_unit_data_fields):**
- Changed from hardcoded fields to configuration-driven
- Now reads Unit Data fields dynamically from config
- Special handling maintained for Product field with change callback

**c) Experiment Form Creation (create_all_sections_dynamically):**
- Added filter to exclude "Unit Data" section from experiment forms
- Unit Data section is rendered separately in left panel only

**d) Section Ordering (get_all_sections):**
- Added "Unit Data" to section_order list
- Positioned after "Basic Information"
- Includes comment noting it's rendered separately

### 4. Configuration Files Updated
All three product configs updated:
- ✅ GNRControlPanelConfig.json
- ✅ CWFControlPanelConfig.json  
- ✅ DMRControlPanelConfig.json

Each now has:
- 5 Unit Data fields properly configured
- Product field with appropriate options
- All metadata (section, type, default, description, required)

## Benefits

### 1. **Extensibility**
- New Unit Data fields can be added via configuration
- No code changes needed to add common fields
- Developer Environment tool can manage Unit Data fields

### 2. **Consistency**
- Unit Data applies to all experiments automatically
- Changes propagate immediately to all experiment tabs
- Reduces data duplication and inconsistency

### 3. **Clarity**
- Clear separation between unit-level and experiment-level data
- Users understand which fields are shared vs. experiment-specific
- Cleaner UI with Unit Data in dedicated left panel section

### 4. **Maintainability**
- Configuration-driven approach
- Easier to add new unit-level common fields
- Changes centralized in config files

## Field Distribution (After Changes)

```
Basic Information         :  4 fields (removed 2 Unit Data fields)
Unit Data                 :  5 fields (NEW section)
Advanced Configuration    :  5 fields (removed 2 Unit Data fields)
Test Configuration        : 15 fields
Voltage & Frequency       :  5 fields
Loops                     :  1 field
Sweep                     :  5 fields
Shmoo                     :  2 fields
Linux                     : 17 fields
Dragon                    : 13 fields
Merlin                    :  5 fields
```

**Total: 77 fields (72 experiment fields + 5 unit data fields)**

## Usage

### Adding New Unit Data Fields

To add a new common field that applies to all experiments:

1. **Update config file** (e.g., GNRControlPanelConfig.json):
```json
"New Common Field": {
    "section": "Unit Data",
    "type": "str",
    "default": "",
    "description": "Description of new field",
    "required": false
}
```

2. **No code changes needed** - the field will automatically:
   - Appear in the Unit Data panel (left side)
   - Apply to all experiments
   - Be manageable via Developer Environment tool

### Verifying Configuration

Run the verification script:
```powershell
python verify_unit_data_configs.py
```

This checks:
- All Unit Data fields are present
- Fields properly moved from other sections
- Field distribution is correct

## Technical Details

### How Unit Data Works:

1. **Rendering**: Unit Data fields render in left panel via `create_unit_data_fields()`
2. **Exclusion**: Experiment forms skip "Unit Data" section via filter in `create_all_sections_dynamically()`
3. **Auto-Apply**: Changes to Unit Data fields automatically propagate to all experiments via `auto_apply_unit_data()`
4. **Persistence**: Unit Data saved with experiments in .tpl files
5. **Priority**: Unit Data overrides experiment-specific values

### Key Methods:

- `create_unit_data_fields()` - Dynamically creates Unit Data input fields from config
- `auto_apply_unit_data()` - Propagates Unit Data to all experiments  
- `create_all_sections_dynamically()` - Creates experiment sections, excludes "Unit Data"
- `get_all_sections()` - Lists all sections including "Unit Data" for ordering

## Verification Results

✅ All 3 product configs verified successfully
✅ 5 Unit Data fields in each config
✅ All fields properly moved from previous sections
✅ Field distribution correct across all sections
✅ No Unit Data fields appearing in experiment sections

## Files Modified

1. `PPV/gui/ExperimentBuilder.py` - Main application logic
2. `PPV/configs/GNRControlPanelConfig.json` - GNR product config
3. `PPV/configs/CWFControlPanelConfig.json` - CWF product config
4. `PPV/configs/DMRControlPanelConfig.json` - DMR product config

## Scripts Created

1. `update_unit_data_configs.py` - Migration script to update all configs
2. `verify_unit_data_configs.py` - Verification script to validate changes
