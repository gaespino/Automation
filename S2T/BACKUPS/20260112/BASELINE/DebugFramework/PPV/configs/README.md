# Control Panel Configuration Files

This directory contains product-specific configuration files for the PPV Experiment Builder.

## Files

### GNRControlPanelConfig.json
**Product:** GNR (Granite Rapids)  
**Description:** Configuration for GNR platform experiments  
**Usage:** Default configuration when Product = GNR

### CWFControlPanelConfig.json
**Product:** CWF (Clearwater Forest)  
**Description:** Configuration for CWF platform experiments  
**Usage:** Auto-loaded when Product = CWF

### DMRControlPanelConfig.json
**Product:** DMR (Diamond Rapids)  
**Description:** Configuration for DMR platform experiments  
**Usage:** Auto-loaded when Product = DMR

## Configuration Structure

Each file contains:

```json
{
    "data_types": {
        /* 76 experiment fields with type definitions */
    },
    "TEST_MODES": ["Mesh", "Slice"],
    "TEST_TYPES": ["Loops", "Sweep", "Shmoo"],
    "CONTENT_OPTIONS": ["Linux", "Dragon", "PYSVConsole"],
    "VOLTAGE_TYPES": ["vbump", "fixed", "ppvc"],
    "TYPES": ["Voltage", "Frequency"],
    "DOMAINS": ["CFC", "IA"],
    "PRODUCT": "GNR|CWF|DMR",
    "DESCRIPTION": "Product-specific description",
    "field_enable_config": {
        /* Product-specific field enabling rules */
    }
}
```

## Field Enable Configuration (NEW in v2.3)

The `field_enable_config` section controls which fields are enabled for each product. This allows easy customization without code changes.

### Format

```json
"field_enable_config": {
    "Field Name": ["Product1", "Product2"],
    "Another Field": ["Product3"]
}
```

### Current Configuration

```json
"field_enable_config": {
    "Pseudo Config": ["GNR"],
    "Disable 2 Cores": ["CWF"],
    "Disable 1 Core": ["DMR"],
    "Core License": ["GNR", "DMR"]
}
```

**Behavior:**
- **Pseudo Config** - Only enabled when Product = GNR, grayed out for CWF/DMR
- **Disable 2 Cores** - Only enabled when Product = CWF, grayed out for GNR/DMR
- **Disable 1 Core** - Only enabled when Product = DMR, grayed out for GNR/CWF
- **Core License** - Enabled when Product = GNR or DMR, grayed out for CWF

**Default:** Fields not listed in `field_enable_config` are enabled for all products.

### Adding New Product-Specific Fields

To make a field product-specific:

1. Add the field to `field_enable_config` in all three JSON files
2. List the products where it should be enabled
3. The UI will automatically gray out the field for other products

Example - Adding a new "Test Feature X" for GNR only:

```json
"field_enable_config": {
    "Pseudo Config": ["GNR"],
    "Disable 2 Cores": ["CWF"],
    "Disable 1 Core": ["DMR"],
    "Core License": ["GNR", "DMR"],
    "Test Feature X": ["GNR"]
}
```

## Field Types

- **str**: String values (paths, names, commands)
- **int**: Integer values (ports, counts, frequencies)
- **float**: Floating-point values (voltages, sweep parameters)
- **bool**: Boolean values (flags, enable/disable)

## Total Fields: 76

### New Fields (Added in v2.0)
- **Fuse File** (str) - External fuse file to be loaded into the system
- **Bios File** (str) - BIOS file to be loaded at experiment start

### Field Categories

1. **Basic Information** (4 fields)
   - Experiment, Test Name, Test Mode, Test Type

2. **Test Configuration** (14 fields)
   - TTL Folder, Scripts File, Post Process, Pass/Fail Strings
   - Test Number, Test Time, Loops, Reset options
   - Core License, 600W Unit, Pseudo Config

3. **Voltage & Frequency** (5 fields)
   - Voltage Type, IA/CFC Voltages, IA/CFC Frequencies

4. **Sweep/Shmoo** (7 fields)
   - Type, Domain, Start, End, Steps, ShmooFile, ShmooLabel

5. **Content** (1 field)
   - Content selection (Linux/Dragon/PYSVConsole)

6. **Linux Configuration** (9 fields)
   - Linux Path, Startup, Commands, Strings, Wait Time
   - Content Lines 0-9

7. **Dragon Configuration** (13 fields)
   - Dragon Content Path, Startup, Commands
   - ULX settings, Product Chop
   - VVAR0-3, VVAR_EXTRA, Content Line

8. **Advanced Configuration** (7 fields)
   - Configuration Mask, Boot Breakpoint, Core settings
   - Stop on Fail, Fuse File, Bios File

9. **Merlin Configuration** (3 fields)
   - Merlin Name, Drive, Path

10. **Unit Data** (4 fields - shared)
    - Visual ID, Bucket, COM Port, IP Address

## Usage in ExperimentBuilder

### Product Selection
1. Select product from **Unit Data** panel dropdown
2. Configuration automatically loads for that product
3. Dropdown options update based on product config

### Config Loading
```python
# Loads product-specific config
self.config_template = self.load_config_template("GNR")
self.config_template = self.load_config_template("CWF")
self.config_template = self.load_config_template("DMR")
```

### Adding New Products
1. Create new JSON file: `{PRODUCT}ControlPanelConfig.json`
2. Copy structure from existing file
3. Update `PRODUCT` and `DESCRIPTION` fields
4. Add product to Unit Data dropdown in `ExperimentBuilder.py`

## Customization

### Product-Specific Options

You can customize dropdown options per product:

```json
{
    "TEST_MODES": ["Mesh", "Slice"],
    "VOLTAGE_TYPES": ["vbump", "fixed", "ppvc", "custom"],
    "CONTENT_OPTIONS": ["Linux", "Dragon", "Custom"]
}
```

### Product-Specific Fields

To add product-specific fields:
1. Add field to `data_types` in product config
2. Update `ExperimentBuilder.py` to create the field
3. Add conditional logic if needed

## Version History

- **v1.0** - Initial configs with 74 fields
- **v2.0** - Added Fuse File and Bios File (76 fields total)
- **v2.0** - Moved from S2T path to PPV/configs folder
- **v2.0** - Added product-specific config support

## Backup

Always backup config files before making changes:
```powershell
Copy-Item PPV/configs/*.json PPV/configs/backup/
```

## Validation

Config files are automatically validated on load. Invalid configs fall back to default template.

---

**Last Updated:** December 8, 2024  
**Maintained By:** Automation Team
