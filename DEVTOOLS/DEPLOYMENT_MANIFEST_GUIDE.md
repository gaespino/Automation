# Production Deployment Manifests Guide

## Overview
This directory contains deployment manifests that define which files should be included/excluded when deploying to production environments. These manifests help ensure that test files, mock implementations, and development-only code are not deployed to production.

## Manifest Files

### 1. `deployment_manifest_debugframework.json`
**Purpose**: Defines production deployment for the DebugFramework module

**Excluded from Production**:
- `TestRun.py` - Test launcher script
- `TestMocks.py` - Mock implementations for testing
- `HardwareMocks.py` - Hardware simulation mocks
- `S2TMocks.py` - S2T mock implementations
- `S2TTestFramework.py` - Test framework utilities
- `MockControlPanel.py` - Mock UI for testing
- `TestControlPanel.py` - Test control panel
- `test_config.py` - Test configuration
- Development notes and reference code in Automation_Flow
- Old/deprecated code files

**Included in Production**:
- Core framework files (SystemDebug.py, TestFramework.py, etc.)
- All ExecutionHandler utilities
- UI components (excluding test/mock files)
- Automation_Flow (excluding dev notes)
- Storage_Handler for database operations
- TTL and EFI files for hardware communication
- PPV integration components
- Shmoos configuration

### 2. `deployment_manifest_s2t.json`
**Purpose**: Defines production deployment for the S2T (System-to-Tester) module

**Excluded from Production**:
- Test files matching `test_*.py` pattern
- Python cache files

**Included in Production**:
- Core S2T files (ConfigsLoader, CoreManipulation, dpmChecks, etc.)
- Logger utilities
- Managers
- Tools
- Fuse handling
- UI components
- EFI Tools
- Product-specific implementations (GNR/CWF/DMR)

**Product-Specific Deployment**:
The `product_specific` folder contains subdirectories for GNR, CWF, and DMR. When deploying to a specific product environment, only deploy the relevant subfolder:
- For GNR: Deploy `product_specific/GNR` only
- For CWF: Deploy `product_specific/CWF` only
- For DMR: Deploy `product_specific/DMR` only

### 3. `deployment_manifest_ppv.json`
**Purpose**: Defines production deployment for the PPV (Post-Processing and Visualization) module

**Excluded from Production**:
- `MCAparser_bkup.py` - Backup/legacy file
- `install_dependencies.bat/py` - Development setup scripts
- `process.ps1` - Development PowerShell script
- `DebugScripts/` - Development debugging scripts
- Test files and Python cache

**Included in Production**:
- Main entry point (run.py)
- API components
- Decoder (with CWF, DMR, GNR subdirectories)
- GUI components
- Parsers
- Utils
- All product configuration files (GNR, CWF, DMR)
- requirements.txt and README.md

**Note**: PPV can be deployed standalone or integrated with DebugFramework.

## Usage with deploy_universal.py

### Manual Filtering
When using the deployment tool, you can:
1. Load the manifest JSON file
2. Use the file list to guide manual selection
3. Filter out test/mock files automatically

### Automatic Integration (Recommended Enhancement)
The deployment tool could be enhanced to:
```python
import json

def load_deployment_manifest(manifest_path):
    """Load deployment manifest configuration"""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def should_include_file(file_path, manifest):
    """Check if file should be included based on manifest"""
    # Check explicit exclusions
    if file_path in manifest['exclude_files']:
        return False
    
    # Check exclude patterns
    for pattern in manifest.get('exclude_patterns', []):
        if fnmatch.fnmatch(file_path, pattern):
            return False
    
    # Check explicit inclusions or directory rules
    # ... implementation details
    
    return True
```

## Quick Reference: Files to EXCLUDE

### DebugFramework - DO NOT DEPLOY:
```
TestRun.py
TestMocks.py
HardwareMocks.py
S2TMocks.py
S2TTestFramework.py
UI/MockControlPanel.py
UI/TestControlPanel.py
UI/test_config.py
UI/old_windows/
ExecutionHandler/Old_code.py
Automation_Flow/dummy_structure.json
Automation_Flow/notes.txt
Automation_Flow/old_interface.py
Automation_Flow/reference_code_old.py
```

### S2T - DO NOT DEPLOY:
```
test_*.py files
product_specific/<non-target-product>/  (deploy only target product)
```

### PPV - DO NOT DEPLOY:
```
MCAparser_bkup.py
install_dependencies.bat
install_dependencies.py
process.ps1
DebugScripts/
```

## Deployment Checklist

### Pre-Deployment
- [ ] Identify target product (GNR, CWF, or DMR)
- [ ] Load appropriate deployment manifest
- [ ] Review exclude patterns
- [ ] Verify all test/mock files are filtered

### During Deployment
- [ ] Scan source files using deployment tool
- [ ] Apply manifest exclusions
- [ ] For S2T: Deploy only target product folder from product_specific/
- [ ] Verify import replacement CSV is loaded if needed
- [ ] Check file rename CSV for product-specific naming

### Post-Deployment
- [ ] Verify no test files deployed (no TestRun.py, no *Mock*.py)
- [ ] Verify no development scripts deployed
- [ ] Verify correct product-specific files deployed
- [ ] Test basic functionality in target environment

## Integration with Existing Tools

### With deploy_universal.py
1. Add "Load Manifest" button to load JSON manifest
2. Auto-filter files based on manifest exclusions
3. Show warning if excluded files are selected
4. Apply product-specific rules for S2T deployment

### With CSV Generation
When generating import replacement or file rename CSVs, reference the manifest to ensure only production files are considered.

## Maintenance

### Updating Manifests
When new files are added to the codebase:
1. Determine if file is production-ready or development-only
2. Add to appropriate manifest section
3. Update this README if new categories are created
4. Test deployment with updated manifest

### Version Control
- Manifests are versioned alongside code
- Changes to module structure require manifest updates
- Review manifests during code reviews for new features

## Examples

### Example 1: Deploy DebugFramework for GNR Production
```bash
Source: S2T/BASELINE/DebugFramework/
Target: <production-path>/GNR/DebugFramework/
Manifest: deployment_manifest_debugframework.json
Product: GNR
Excludes: All test/mock files per manifest
```

### Example 2: Deploy S2T for CWF Production
```bash
Source: S2T/BASELINE/S2T/
Target: <production-path>/CWF/S2T/
Manifest: deployment_manifest_s2t.json
Product: CWF
Special: Only deploy product_specific/CWF/ folder
Excludes: product_specific/GNR/, product_specific/DMR/, test files
```

### Example 3: Deploy PPV Standalone
```bash
Source: PPV/
Target: <production-path>/PPV/
Manifest: deployment_manifest_ppv.json
Excludes: DebugScripts/, backup files, installation scripts
Includes: All three product configs (GNR, CWF, DMR)
```

## Support

For questions or issues with deployment manifests:
1. Review the manifest JSON file for the module
2. Check exclusion patterns match your requirements
3. Test deployment in non-production environment first
4. Update manifest if requirements change
