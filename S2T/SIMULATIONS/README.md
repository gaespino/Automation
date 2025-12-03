# S2T Mock Simulations

This directory contains mock simulations for testing S2T framework functions without requiring hardware or pythonsv connections.

## Directory Structure

```
SIMULATIONS/
├── BASE/           # Mocks for BASELINE scripts (GNR, CWF)
│   └── (empty - ready for future mocks)
│
└── DMR/            # Mocks for BASELINE_DMR scripts (DMR product)
    ├── mock_dpmChecks.py      # Complete mock implementation
    ├── test_logger.py         # 10 comprehensive tests
    ├── examples.py            # 8 usage examples
    ├── verify.py              # Quick verification script
    ├── mock_config.json       # Configuration file
    ├── README.md              # Full documentation
    ├── QUICKSTART.md          # Quick start guide
    └── SUMMARY.md             # Implementation summary
```

## Available Mocks

### BASE (BASELINE) - GNR/CWF with FILE GENERATION
**Status**: ✅ Complete with Actual File Generation  
**Target**: `BASELINE/S2T/dpmChecks.py` - `logger()` function  
**Features**:
- ✨ **ACTUAL FILE GENERATION** - Creates real Excel, CSV, JSON files
- 🖥️ **Working Tkinter UI** - Interactive form for data entry
- 🔍 **MCA Bank Simulation** - Realistic error scenarios
- 11 automated test cases with file verification
- 8 example scenarios with file generation
- Complete file content validation
- JSON configuration
- Full documentation

**Quick Start**:
```powershell
cd BASE
python verify.py           # Quick verification with file generation
python test_logger.py      # Run all tests (creates test_output/)
python examples.py --all   # Run all examples (creates example_output/)
python examples.py --ui    # Try interactive UI
```

**Generated Files**:
- 📊 Excel TileView Reports (formatted, with MCA data, error highlighting)
- 📄 MCA CSV Data (complete bank information)
- 🐉 Dragon Memory Dumps (simulated memory content)
- ⚙️ Framework JSON (test configuration and results)
- 📝 Memory Check Reports (validation output)

**Key Features**:
- `logger()` - Generates actual files (Excel, CSV, JSON, TXT)
- `visual_str()` - Visual ID retrieval
- `qdf_str()` - QDF string retrieval  
- `getWW()` - Work week calculation
- `request_unit_info()` - Unit information
- `fuses()` - Fuse mask operations
- `powercycle()` - Power control
- Working Tkinter UI for interactive testing
- MCA bank simulation with realistic errors
- Complete pythonsv (sv) simulation
- Complete IPC simulation

### DMR (BASELINE_DMR)
**Status**: ✅ Complete (Basic Mock)
**Target**: `BASELINE_DMR/S2T/dpmChecks.py` - `logger()` function  
**Features**:
- Complete mock of all logger dependencies
- 10 automated test cases
- 8 example scenarios
- Interactive testing support
- JSON configuration
- Full documentation

**Quick Start**:
```powershell
cd DMR
python test_logger.py      # Run all tests
python examples.py --all   # Run all examples
python verify.py           # Quick verification
```

**Key Mocks**:
- `logger()` - Main logging function simulation
- `visual_str()` - Visual ID retrieval
- `qdf_str()` - QDF string retrieval
- `getWW()` - Work week calculation
- `request_unit_info()` - Unit information
- `fuses()` - Fuse mask operations
- `powercycle()` - Power control
- Complete pythonsv (sv) simulation
- Complete IPC simulation
- Configuration object

## Usage

### Option 1: Run Tests
```powershell
cd DMR
python test_logger.py
```

### Option 2: Run Examples
```powershell
cd DMR
python examples.py
```

### Option 3: Import and Use
```python
import sys
sys.path.insert(0, r'c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR')
import mock_dpmChecks as dpm

# Use any mocked function
result = dpm.logger(TestName='MyTest', Testnumber=1)
visual = dpm.visual_str()
qdf = dpm.qdf_str()
```

## Benefits

✅ **No Hardware Required**: Test without physical units  
✅ **Fast Execution**: No waiting for hardware operations  
✅ **Reproducible**: Consistent results every time  
✅ **Debugging**: Clear visibility into execution flow  
✅ **Isolated Testing**: Test functions independently  
✅ **CI/CD Ready**: Integrate into automated pipelines  
✅ **Documentation**: Serves as usage examples  

## Creating New Mocks

### For DMR (Add to existing)
1. Edit `DMR/mock_dpmChecks.py`
2. Add new mock class or function
3. Update `DMR/test_logger.py` with tests
4. Add examples to `DMR/examples.py`

### For GNR/CWF (New product)
1. Copy `DMR/` folder to `BASE/`
2. Update `MockConfig.SELECTED_PRODUCT`
3. Adjust product-specific configurations
4. Update mock responses for product differences
5. Update documentation

### Template Structure
```
PRODUCT/
├── mock_{module}.py       # Mock implementation
├── test_{function}.py     # Test suite
├── examples.py            # Usage examples
├── verify.py              # Quick verification
├── mock_config.json       # Configuration
├── README.md              # Full documentation
├── QUICKSTART.md          # Quick start
└── SUMMARY.md             # Implementation summary
```

## Mock Guidelines

### What to Mock
- External dependencies (pythonsv, IPC, etc.)
- Hardware access functions
- File I/O operations that need hardware data
- Network operations
- Long-running operations

### What NOT to Mock
- Pure Python logic
- Data transformations
- Calculations
- String operations
- Built-in Python functions

### Mock Best Practices
1. **Realistic Behavior**: Mocks should behave like the real thing
2. **Print Statements**: Add visibility for debugging
3. **Configurable**: Use JSON config for customization
4. **Documented**: Include docstrings and comments
5. **Tested**: Create comprehensive test suites
6. **Examples**: Provide usage examples

## Documentation

Each mock directory should include:
- **README.md**: Comprehensive documentation
- **QUICKSTART.md**: Quick start guide (3 steps max)
- **SUMMARY.md**: Implementation summary
- **Inline Comments**: Code documentation
- **Examples**: Working code examples

## Testing

Each mock should have:
- **Test Suite**: Comprehensive automated tests
- **Examples**: Multiple usage scenarios
- **Verification**: Quick check script
- **Coverage**: Test all parameters and paths

## Integration

### With Real Code
```python
# Replace real modules with mocks
import sys
sys.path.insert(0, r'path\to\SIMULATIONS\DMR')
import mock_dpmChecks

sys.modules['gcm'] = mock_dpmChecks.gcm
sys.modules['dpmlog'] = mock_dpmChecks.dpmlog
sys.modules['dpmtileview'] = mock_dpmChecks.dpmtileview

# Now import real code with mocked dependencies
import dpmChecks
```

### In CI/CD Pipelines
```yaml
# Example GitHub Actions
- name: Run Mock Tests
  run: |
    cd S2T/SIMULATIONS/DMR
    python test_logger.py
```

## Current Status

| Product | Module | Function | Status | Tests | Examples | Docs | File Gen |
|---------|--------|----------|--------|-------|----------|------|----------|
| GNR/CWF | dpmChecks | logger() | ✅ | 11 | 8 | ✅ | ✅ Real |
| DMR | dpmChecks | logger() | ✅ | 10 | 8 | ✅ | ❌ Mock |

## Future Enhancements

### Planned Features
- [ ] Mock for pseudo_bs() function
- [ ] Mock for fuses() function complete workflow
- [ ] Mock for burnin() function
- [ ] Mock for RA test functions
- [ ] Mock for voltage/ratio functions
- [ ] GNR product mocks (BASE folder)
- [ ] CWF product mocks (BASE folder)
- [ ] Network simulation for uploads
- [ ] Performance metrics
- [ ] Error injection for negative testing

### Enhancement Ideas
- Visual test report generation
- Mock data file generation
- Recording and playback of real hardware data
- Integration with pytest
- Code coverage analysis
- Performance benchmarking

## Support

### Getting Help
1. Check the README.md in the specific product folder
2. Review QUICKSTART.md for common issues
3. Examine examples.py for usage patterns
4. Run test suite to verify functionality
5. Check inline code comments

### Reporting Issues
If you find issues with mocks:
1. Verify the real function signature hasn't changed
2. Check if configuration needs updating
3. Run verification script
4. Review test results

### Contributing
To add new mocks or improve existing ones:
1. Follow the template structure
2. Include comprehensive tests
3. Add usage examples
4. Document thoroughly
5. Verify all tests pass

## Version History

### v1.0 - December 2, 2025
- ✅ Initial DMR mock implementation
- ✅ Complete logger() function mock
- ✅ 10 comprehensive tests
- ✅ 8 usage examples
- ✅ Full documentation
- ✅ Configuration support

### Future Versions
- v1.1: Add more DMR function mocks
- v2.0: Add GNR/CWF mocks in BASE folder
- v3.0: Advanced features (recording, playback, etc.)

---

**Location**: `c:\Git\Automation\Automation\S2T\SIMULATIONS\`  
**Purpose**: Mock testing environment for S2T framework  
**Status**: Active Development  
**Last Updated**: December 2, 2025
