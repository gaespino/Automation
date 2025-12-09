# Field Configuration Enhancement Guide

## Overview

The ExperimentBuilder and Developer Environment have been enhanced with a comprehensive field configuration system that allows developers to easily add, edit, and remove fields with full metadata including section assignment, type, default values, descriptions, and conditional display rules.

## What Changed

### 1. Configuration Structure Evolution

**OLD Format** (`data_types`):
```json
{
    "data_types": {
        "CPU Frequency": ["int"],
        "Test Name": ["str"]
    }
}
```

**NEW Format** (`field_configs`):
```json
{
    "field_configs": {
        "CPU Frequency": {
            "section": "Voltage & Frequency",
            "type": "int",
            "default": 0,
            "description": "CPU frequency in MHz",
            "required": false,
            "options": []
        },
        "Test Name": {
            "section": "Basic Information",
            "type": "str",
            "default": "",
            "description": "Unique test identifier",
            "required": true
        }
    }
}
```

### 2. Field Metadata

Each field now supports:
- **section**: Which UI section to place the field in
- **type**: Data type (str, int, float, bool)
- **default**: Default value for the field
- **description**: Tooltip/help text shown to users
- **required**: Whether field must be filled
- **options**: Dropdown options (for combobox fields)
- **condition**: Conditional display rules (e.g., show only when Test Type = "Loops")

## Available Sections

The following sections are available for field placement:

1. **Basic Information** - Core experiment identifiers
2. **Advanced Configuration** - Advanced settings, COM ports, IPs
3. **Test Configuration** - Test-specific settings
4. **Voltage & Frequency** - Power and frequency controls
5. **Loops** - Loop configuration (conditional: Test Type = Loops)
6. **Sweep** - Sweep parameters (conditional: Test Type = Sweep)
7. **Shmoo** - Shmoo configuration (conditional: Test Type = Shmoo)
8. **Linux** - Linux content settings (conditional: Content = Linux)
9. **Dragon** - Dragon content settings (conditional: Content = Dragon)
10. **Merlin** - Merlin configuration

## Using the Developer Environment

### Adding a New Field

1. **Launch Developer Environment**:
   - From ExperimentBuilder: Click `Utils` → `🛠 Developer Environment`
   - From command line: `python PPV\utils\DeveloperEnvironment.py`

2. **Navigate to ExperimentBuilder Config**:
   - Click `📝 ExperimentBuilder` in the sidebar

3. **Add New Field**:
   - Click `➕ Add Field` button
   - Fill in the dialog:
     - **Field Name**: e.g., "CPU Temperature"
     - **Field Type**: Select from dropdown (str, int, float, bool)
     - **Section**: Choose target section from dropdown
     - **Default Value**: Type-appropriate default (e.g., 0, "", false)
     - **Description**: User-friendly description for tooltip

4. **Export Configuration**:
   - Click `💾 Export Config`
   - Save to a JSON file (e.g., `experiment_config.json`)

5. **Apply to ExperimentBuilder**:
   - Copy exported file to `PPV/configs/GNRControlPanelConfig.json`
   - Or: Load via File Operations → Load Configuration in ExperimentBuilder

### Editing Existing Fields

1. Select field from the list on the left
2. Use the JSON editor on the right to modify field properties directly
3. Export config when done

### Deleting Fields

1. Select field from the list
2. Click `🗑 Delete Field`
3. Confirm deletion
4. Export config to save changes

## How ExperimentBuilder Uses Field Configs

### Dynamic Section Creation

When ExperimentBuilder loads, it:

1. Loads the configuration from `PPV/configs/GNRControlPanelConfig.json`
2. If old `data_types` format is found, migrates to `field_configs` automatically
3. Reads all unique sections from field_configs
4. Creates UI sections in defined order
5. Populates each section with fields that have matching `section` property

### Backward Compatibility

The system maintains full backward compatibility:
- Old `data_types` configs are automatically migrated
- Migrated fields default to "Basic Information" section
- All existing functionality continues to work

### Example: Adding "CPU Temperature" Field

**Step 1**: Add in Developer Environment
```json
"CPU Temperature": {
    "section": "Voltage & Frequency",
    "type": "int",
    "default": 0,
    "description": "Current CPU temperature in Celsius",
    "required": false
}
```

**Step 2**: Export config and copy to PPV/configs/

**Step 3**: Restart ExperimentBuilder

**Result**: "CPU Temperature" field now appears in the "Voltage & Frequency" section automatically!

## Field Configuration Best Practices

### 1. Choose Appropriate Sections

- Group related fields together
- Use conditional sections for Test Type or Content specific fields
- Keep Basic Information minimal (core identifiers only)

### 2. Provide Clear Descriptions

Good:
```json
"description": "Number of test iterations to execute (1-1000)"
```

Bad:
```json
"description": "Loops field"
```

### 3. Set Sensible Defaults

```json
"Test Mode": {
    "type": "str",
    "default": "Mesh",  // Most common value
    "options": ["Mesh", "Slice"]
}
```

### 4. Use Conditional Display

For fields that only apply in certain scenarios:
```json
"Loops": {
    "section": "Loops",
    "condition": {
        "field": "Test Type",
        "value": "Loops"
    }
}
```

### 5. Specify Options for Comboboxes

```json
"Voltage Type": {
    "type": "str",
    "default": "vbump",
    "options": ["vbump", "fixed", "ppvc"]
}
```

## Configuration File Locations

- **Default Template**: Built into ExperimentBuilder's `get_default_template()` method
- **Product Configs**: `PPV/configs/{Product}ControlPanelConfig.json`
- **User Configs**: Can be saved/loaded via File Operations menu

## Migration Path

### For Existing Configurations

1. Old configs with `data_types` will auto-migrate on load
2. All fields default to "Basic Information" section
3. Use Developer Environment to reassign fields to proper sections
4. Export updated configuration
5. Replace old config file

### For New Fields

1. Always add fields via Developer Environment
2. Use the new `field_configs` structure
3. Specify all metadata (section, type, default, description)
4. Test in ExperimentBuilder before committing

## Troubleshooting

### Field Not Appearing

- Check `section` matches an available section name exactly
- Verify field_configs structure is correct in JSON
- Check for conditional display rules that might be hiding it

### Field in Wrong Section

- Open Developer Environment
- Find field in list
- Edit JSON on right to change `"section"` property
- Export and reload

### Migration Issues

- If old config doesn't migrate properly:
  - Check JSON syntax is valid
  - Ensure `data_types` structure matches expected format
  - Use Developer Environment to view/fix issues

## Version Control Integration

### Recommended Workflow

1. **Edit configs in Developer Environment**
2. **Export to JSON file**
3. **Review changes** using git diff
4. **Commit** configuration changes
5. **Share** with team via version control

### Example Git Workflow

```powershell
# Edit configs in Developer Environment
python PPV\utils\DeveloperEnvironment.py

# Export to PPV/configs/GNRControlPanelConfig.json

# Review changes
git diff PPV/configs/GNRControlPanelConfig.json

# Commit if good
git add PPV/configs/GNRControlPanelConfig.json
git commit -m "Add CPU Temperature field to Voltage & Frequency section"
```

## API Reference

### Field Config Schema

```typescript
{
    "field_configs": {
        "[field_name]": {
            "section": string,        // Required: Section name
            "type": string,           // Required: "str" | "int" | "float" | "bool"
            "default": any,           // Required: Type-appropriate default
            "description": string,    // Required: User-friendly description
            "required": boolean,      // Optional: Is field required?
            "options": string[],      // Optional: For dropdown/combobox
            "condition": {            // Optional: Conditional display
                "field": string,      // Field to check
                "value": string       // Value to match
            }
        }
    }
}
```

### Migration Function

```python
def migrate_config_format(config: dict) -> dict:
    """
    Migrates old data_types format to new field_configs format
    
    Args:
        config: Configuration dictionary (either format)
    
    Returns:
        Configuration in field_configs format
    """
```

### Section Creation

```python
def create_dynamic_section(parent, widgets, start_row, section_name, icon="🔹"):
    """
    Dynamically creates a UI section with all fields that have matching section property
    
    Args:
        parent: Parent widget
        widgets: Dict to store field widgets
        start_row: Starting grid row
        section_name: Name of section to create
        icon: Icon emoji for section header
    
    Returns:
        Next available row number
    """
```

## Future Enhancements

Potential improvements for future versions:

1. **Field Dependencies**: Show/hide fields based on multiple conditions
2. **Validation Rules**: Min/max values, regex patterns for strings
3. **Custom Widgets**: Browse buttons, color pickers, etc.
4. **Field Groups**: Sub-sections within sections
5. **Templates**: Predefined field sets for common scenarios
6. **Field Reordering**: Drag-and-drop field ordering within sections
7. **Bulk Operations**: Add/edit multiple fields at once
8. **Search & Filter**: Advanced search in Developer Environment
9. **Change History**: Track configuration changes over time
10. **Import/Export Formats**: Support CSV, Excel formats

## Summary

The enhanced field configuration system provides:

✅ **Easy Field Management**: Add/edit/remove fields without code changes  
✅ **Rich Metadata**: Descriptions, defaults, sections, conditions  
✅ **Backward Compatible**: Old configs auto-migrate  
✅ **Dynamic UI**: Sections created automatically from config  
✅ **Developer Friendly**: Standalone tool for configuration management  
✅ **Version Control Ready**: JSON format works great with git  

This makes ExperimentBuilder much more maintainable and extensible!
