# PPV Developer Environment v1.0

## Overview

The PPV Developer Environment is a comprehensive configuration management tool designed for developers working on the PPV Tools Hub. It provides a centralized interface for managing field configurations, data structures, and tool templates across all PPV tools.

## Features

### 🔧 Tool Configuration Managers

1. **ExperimentBuilder Configuration**
   - View and edit all field definitions
   - Add/edit/delete fields with type safety
   - Search and filter fields
   - Real-time JSON editor with validation
   - Export/import configurations for version control

2. **Framework Parser Configuration**
   - Configure framework data structures
   - Manage parsing rules and patterns

3. **MCA Parser Configuration**
   - Configure MCA analysis fields
   - Define error detection patterns

4. **Overview Analyzer Configuration**
   - Configure overview metrics
   - Define analysis thresholds

5. **PPV Loops Parser Configuration**
   - Configure loop structure definitions
   - Define iteration patterns

6. **Decoder Configurations**
   - Manage decoder configurations
   - Configure bucketing rules

### 📁 Template Generator

Generate boilerplate code for new tools:
- **GUI Tool Template**: Standard layout with modern UI
- **Parser Template**: Standard structure with common methods
- **Analyzer Template**: Analysis framework with standard methods

### ✓ Configuration Validator

Comprehensive validation of all PPV tool configurations:
- Field definition validation
- File structure verification
- Dependency checking
- Configuration consistency checks

### ⚡ Quick Actions

- **Open Config Folder**: Direct access to configuration directory
- **Backup All Configs**: Create timestamped backups
- **Refresh All**: Reload all configurations

## Usage

### Launching Developer Environment

**From ExperimentBuilder:**
1. Open ExperimentBuilder
2. Click Utils → "🛠 Developer Environment"

**Note:** The Developer Environment is located in `PPV/utils/` folder (not in `PPV/gui/`), as it's a development utility tool rather than a production GUI tool.

**From Command Line:**
```powershell
cd C:\Git\Automation\Automation
.\.venv\Scripts\Activate.ps1
python PPV\utils\DeveloperEnvironment.py
```

**From Python:**
```python
from PPV.utils.DeveloperEnvironment import DeveloperEnvironmentGUI
app = DeveloperEnvironmentGUI()
app.run()
```

### Managing ExperimentBuilder Fields

1. Click **📝 ExperimentBuilder** in the sidebar
2. View all fields in the left panel (searchable)
3. Use toolbar buttons:
   - **💾 Export Config**: Save to JSON file
   - **📂 Import Config**: Load from JSON file
   - **➕ Add Field**: Add new field with type
   - **✏️ Edit Field**: Modify existing field
   - **🗑 Delete Field**: Remove field

### Adding a New Field

1. Click **➕ Add Field**
2. Fill in the dialog:
   - **Field Name**: e.g., "CPU Temperature"
   - **Field Type**: str, int, float, or bool
   - **Section**: Which UI section to place it in
   - **Description**: Tooltip/help text
3. Click **✓ Add Field**
4. Export configuration to save changes
5. Manually add UI code in appropriate `create_*_section` method

### Exporting Configuration

1. Make your changes in the Developer Environment
2. Click **💾 Export Config**
3. Save to `field_config.json` (or custom name)
4. Commit to version control

### Importing Configuration

1. Click **📂 Import Config**
2. Select JSON configuration file
3. Review changes in confirmation dialog
4. Confirm to apply changes
5. Restart application to see changes

### Version Control Workflow

```bash
# Export current config
# Use Developer Environment: Export Config → field_config.json

# Add to git
git add field_config.json
git commit -m "Add CPU Temperature field to ExperimentBuilder"
git push

# On another machine
git pull

# Import config
# Use Developer Environment: Import Config → field_config.json
# Restart application
```

## Configuration File Structure

### ExperimentBuilder Config (`field_config.json`)

```json
{
  "data_types": {
    "Field Name": ["type"],
    "Test Name": ["str"],
    "Test Mode": ["str"],
    "Loops": ["int"],
    "Voltage IA": ["float"],
    "Reset": ["bool"]
  },
  "TEST_MODES": ["Mesh", "Slice"],
  "TEST_TYPES": ["Loops", "Sweep", "Shmoo"],
  "CONTENT_OPTIONS": ["Linux", "Dragon", "PYSVConsole"],
  "VOLTAGE_TYPES": ["vbump", "fixed", "ppvc"],
  "TYPES": ["Voltage", "Frequency"],
  "DOMAINS": ["CFC", "IA"]
}
```

### Field Types

- **str**: String values (text, paths, commands)
- **int**: Integer values (counts, ports, numbers)
- **float**: Decimal values (voltages, frequencies with decimals)
- **bool**: Boolean values (true/false checkboxes)

### Sections

Fields are organized into these sections:
- **Basic Information**: Core test identification
- **Test Configuration**: Test execution settings
- **Advanced Configuration**: Expert settings
- **Voltage & Frequency**: Power/clock settings
- **Loops**: Loop configuration (conditional)
- **Sweep**: Sweep configuration (conditional)
- **Shmoo**: Shmoo configuration (conditional)
- **Linux**: Linux content (conditional)
- **Dragon**: Dragon content (conditional)
- **Merlin**: Merlin configuration (conditional)

## Development Guidelines

### Adding New Fields

1. **Design Phase**: Determine field name, type, section, and purpose
2. **Add to Config**: Use Developer Environment to add field definition
3. **Export Config**: Save to version control
4. **UI Implementation**: Add widget in appropriate section method
5. **Data Handling**: Ensure field is included in save/load logic
6. **Testing**: Test with all field types and edge cases
7. **Documentation**: Update user documentation

### Modifying Existing Fields

⚠️ **Caution**: Changing field names or types can break existing configurations!

1. Consider backwards compatibility
2. Provide migration path for old configs
3. Update all references in code
4. Test with existing configuration files
5. Document breaking changes

### Best Practices

- ✅ Use descriptive field names (e.g., "CPU Frequency" not "cpufreq")
- ✅ Choose appropriate types (int for counts, float for measurements)
- ✅ Group related fields in same section
- ✅ Export configs regularly for backup
- ✅ Commit config changes separately from code changes
- ✅ Test configurations before pushing
- ⚠️ Never delete fields that existing configs depend on
- ⚠️ Don't change field types without migration plan

## Troubleshooting

### "Developer Environment not found"

The launcher looks for `DeveloperEnvironment.py` in the same directory as `ExperimentBuilder.py`. Ensure:
```
PPV/gui/
├── ExperimentBuilder.py
└── DeveloperEnvironment.py
```

### "Configuration import failed"

Check that JSON file has required keys:
- `data_types`
- `TEST_MODES`
- `TEST_TYPES`
- `CONTENT_OPTIONS`

### "Field not showing in UI"

After adding a field:
1. Verify it's in the exported config
2. Check if UI code was added to `create_*_section` method
3. Restart application to reload config

### Changes not persisting

1. Ensure you exported the config after changes
2. Check file was saved to correct location
3. Verify application restarted to reload config

## Architecture

### Separation of Concerns

**ExperimentBuilder** (Production Tool):
- User-facing experiment configuration
- Field-based data entry
- JSON export for test execution
- Optimized for daily workflow

**Developer Environment** (Development Tool):
- Developer-facing configuration management
- Meta-configuration of tools
- Template generation
- Optimized for tool maintenance

### Benefits of Separation

1. **Clean Interface**: Users don't see developer tools
2. **Better Organization**: Development vs. production concerns separated
3. **Independent Updates**: Can update dev tools without affecting production
4. **Reduced Complexity**: Each tool focused on its purpose
5. **Professional Appearance**: Production tools look polished

## Future Enhancements

### Planned Features

- [ ] Code generation for new sections
- [ ] Automatic UI widget generation
- [ ] Field dependency management
- [ ] Configuration diffing and merging
- [ ] Multi-tool configuration sync
- [ ] Configuration history and rollback
- [ ] Field usage analytics
- [ ] Automated migration scripts
- [ ] Configuration templates library
- [ ] Real-time collaboration features

### Contributing

When adding features to Developer Environment:

1. Keep it developer-focused (not end-user)
2. Maintain consistency with existing UI patterns
3. Add validation for all operations
4. Provide clear error messages
5. Update this README
6. Test with all supported tools

## Support

For issues or questions:
1. Check this README
2. Review configuration file structure
3. Test with exported/imported configs
4. Check application logs
5. Contact development team

## Version History

### v1.0 (Current)
- Initial release
- ExperimentBuilder configuration manager
- Field add/edit/delete functionality
- Configuration export/import
- Template generator framework
- Configuration validator
- Quick actions (backup, refresh, open folder)

---

**Note**: This tool is for developers only. End users should use the production tools (ExperimentBuilder, parsers, etc.) directly.
