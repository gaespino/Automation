# PPV Experiment Builder

## Overview

The **PPV Experiment Builder** is a user-friendly GUI tool for creating and managing experiment configurations that can be consumed by the Debug Framework Control Panel. It simplifies the process of building complex JSON configuration files by providing an intuitive interface with validation, templates, and import/export capabilities.

## Features

### Core Capabilities
- **Visual Experiment Editor**: Create and edit experiments using a tabbed interface with organized fields
- **Import from Excel**: Convert existing Excel-based experiment configurations to JSON format
- **Import from JSON**: Load and edit existing JSON experiment files
- **Export to JSON**: Generate Control Panel-compatible JSON configuration files
- **Experiment Management**: Add, delete, duplicate, and search experiments
- **Real-time Validation**: Validate field values and experiment configurations
- **JSON Preview**: Live preview of generated JSON structure

### Interface Tabs

#### 1. **Basic Info**
- Experiment enable/disable toggle
- Test name and identifier
- Test mode (Mesh/Slice)
- Test type (Loops/Sweep/Shmoo)
- Visual ID and bucket assignment

#### 2. **Test Config**
- COM port and IP address configuration
- TTL folder and scripts file paths
- Pass/Fail string definitions
- Test timing parameters
- Reset and FastBoot options

#### 3. **Voltage/Freq**
- Voltage type selection (vbump/fixed/ppvc)
- IA and CFC voltage settings
- Frequency configuration
- Sweep/Shmoo parameters (Type, Domain, Start, End, Steps)

#### 4. **Content**
- Content type selection (Linux/Dragon/PYSVConsole)
- Linux-specific configuration
- Dragon-specific configuration
- ULX path and CPU settings

#### 5. **Advanced**
- Debug mask configuration
- Boot breakpoint settings
- Core checking options
- Post-processing scripts

#### 6. **JSON Preview**
- Live JSON preview
- Copy to clipboard functionality
- Formatted output display

## Usage

### Launching the Tool

#### From PPV Tools Hub:
1. Run `python run.py` in the PPV folder
2. Click on the "Experiment Builder" card

#### Standalone Mode:
```bash
cd c:\Git\Automation\Automation\PPV
python run_experiment_builder.py
```

### Creating a New Experiment

1. **Click the "+" button** in the left panel to create a new experiment
2. **Edit fields** in the tabbed interface:
   - Navigate through tabs to configure all parameters
   - Use dropdown menus for predefined options
   - Browse buttons (📁) for file/folder paths
   - Tooltips provide field descriptions on hover
3. **Preview JSON** in the "JSON Preview" tab
4. **Save** the experiment automatically when switching to another experiment

### Importing from Excel

1. **Click "Import from Excel"** at the bottom
2. Select your `.xlsx` file
3. Choose import mode:
   - **Merge**: Keep existing experiments and add new ones
   - **Replace**: Replace all experiments with imported data
4. Excel file format:
   - Each sheet represents one experiment
   - Column A: Field names
   - Column B: Field values

### Importing from JSON

1. **Click "Import from JSON"** at the bottom
2. Select your `.json` file
3. Choose import mode (Merge or Replace)
4. JSON format must match Control Panel structure:
```json
{
    "Experiment_Name_1": {
        "Experiment": "Enabled",
        "Test Name": "Test_1",
        "Test Mode": "Mesh",
        ...
    },
    "Experiment_Name_2": {
        ...
    }
}
```

### Exporting to JSON

1. **Click "Export to JSON"** at the bottom
2. Choose save location and filename
3. Generated JSON file is ready to use with Control Panel

### Managing Experiments

- **Add**: Click "+" button
- **Delete**: Select experiment, click "-" button
- **Duplicate**: Select experiment, click "📋" button
- **Search**: Type in the search box to filter experiments
- **Rename**: Edit "Test Name" field (experiment key updates automatically)

### Validation

**Automatic Validation:**
- Numeric fields validated for correct data types
- IP addresses checked for valid format
- Required fields highlighted if empty

**Manual Validation:**
1. Click "Validate All" button
2. Review validation report
3. Fix any issues highlighted in the report

## File Format Compatibility

### Control Panel JSON Format

The tool generates JSON files compatible with the Debug Framework Control Panel. The configuration structure follows the `GNRControlPanelConfig.json` template with all standard fields:

**Key Fields:**
- `Experiment`: "Enabled" or "Disabled"
- `Test Name`: Unique experiment identifier
- `Test Mode`: "Mesh" or "Slice"
- `Test Type`: "Loops", "Sweep", or "Shmoo"
- Hardware settings (COM Port, IP Address, Visual ID, Bucket)
- Test parameters (voltage, frequency, timing)
- Content configuration (Linux, Dragon, PYSVConsole)
- Advanced options (masks, breakpoints, post-processing)

### Excel Import Format

For Excel imports, the tool expects:
- **One sheet per experiment** (sheet name becomes experiment name)
- **Column structure:**
  - Column A: Field names (matching Control Panel fields)
  - Column B: Field values
- **Header row optional** (automatically skipped if detected)

Example Excel structure:
```
| Field Name           | Value              |
|---------------------|--------------------|
| Experiment          | Enabled            |
| Test Name           | My_Test            |
| Test Mode           | Mesh               |
| Test Type           | Loops              |
| COM Port            | 8                  |
| Visual ID           | 75857N7H00175      |
| ...                 | ...                |
```

## Configuration Template

The tool automatically loads field definitions from:
- `S2T\BASELINE\DebugFramework\UI\GNRControlPanelConfig.json`
- `S2T\BASELINE_DMR\DebugFramework\UI\GNRControlPanelConfig.json`

If not found, it uses a built-in default template with all standard fields.

## Tips and Best Practices

1. **Use Descriptive Names**: Give experiments clear, descriptive names for easy identification
2. **Leverage Duplication**: Create a template experiment and duplicate it for variations
3. **Validate Before Export**: Always run "Validate All" before exporting
4. **Preview JSON**: Check the JSON Preview tab to ensure correct formatting
5. **Save Regularly**: Export to JSON periodically to avoid data loss
6. **Organize by Type**: Use search feature to filter experiments by type or characteristics
7. **Test Incrementally**: Start with basic fields, test with Control Panel, then add complexity

## Integration with Control Panel

To use generated JSON files with the Debug Framework Control Panel:

1. **Export** your experiments from the Experiment Builder
2. **Save** the JSON file to a known location
3. **Launch** the Debug Framework Control Panel
4. **Click** "Load Experiments" in the Control Panel
5. **Select** your exported JSON file
6. Experiments will populate in the Control Panel interface

## Troubleshooting

### Import Issues

**Problem**: Excel import fails
- **Solution**: Ensure Excel file format matches expected structure (Field | Value columns)
- **Solution**: Check that sheet names don't contain special characters

**Problem**: JSON import shows "Invalid Format"
- **Solution**: Verify JSON is valid (use JSON validator)
- **Solution**: Ensure top-level structure is a dictionary of experiments

### Validation Errors

**Problem**: COM Port validation error
- **Solution**: Ensure value is numeric and between 0-256

**Problem**: IP Address invalid
- **Solution**: Use standard IPv4 format (e.g., 192.168.0.2)

### Export Issues

**Problem**: Can't export JSON
- **Solution**: Ensure you have write permissions to the target directory
- **Solution**: Close any programs that might have the file open

## Version History

- **v1.0** (2024-12-08): Initial release
  - Full experiment editor with tabbed interface
  - Excel and JSON import/export
  - Validation and preview features
  - Integration with PPV Tools Hub

## Support

For issues or feature requests:
1. Check the validation report for common issues
2. Verify JSON format compatibility with Control Panel
3. Review the example experiments in test files
4. Contact the automation team for assistance

## Related Tools

- **Debug Framework Control Panel**: Consumes the JSON files generated by this tool
- **PPV Tools Hub**: Centralized launcher for all PPV automation tools
- **Automation Flow Designer**: Visual flow design for experiment sequencing

---

**PPV Experiment Builder** - Simplifying experiment configuration management for Debug Framework automation.
