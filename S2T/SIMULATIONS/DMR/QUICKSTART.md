# Quick Start Guide - DPMChecks Logger Mock Testing

## Overview
This mock simulation environment allows testing of the `logger` function from `dpmChecks.py` without requiring actual hardware or pythonsv connections.

## Quick Start (3 Simple Steps)

### 1. Run the Test Suite
```powershell
cd c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR
python test_logger.py
```

### 2. Try Examples
```powershell
# Run all examples
python examples.py --all

# Run specific example
python examples.py --example 1
```

### 3. Interactive Testing
```powershell
python
```
```python
import sys
sys.path.insert(0, r'c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR')
import mock_dpmChecks as dpm

# Basic test
dpm.logger(TestName='MyTest', Testnumber=1)

# With parameters
dpm.logger(
    visual='QVRX12345678',
    qdf='L0_DMRAP_XCC',
    TestName='DetailedTest',
    Testnumber=2,
    debug_mca=1,
    chkmem=1
)
```

## File Structure
```
S2T/SIMULATIONS/DMR/
├── mock_dpmChecks.py    # Main mock module
├── test_logger.py       # Comprehensive test suite (10 tests)
├── examples.py          # 8 example scenarios
├── mock_config.json     # Configuration for mock behavior
├── README.md            # Detailed documentation
└── QUICKSTART.md        # This file
```

## What Gets Mocked

### Core Modules
- ✅ **gcm** (CoreManipulation) - System status, fuse operations
- ✅ **dpmlog** (Logger UI) - User interface functionality
- ✅ **dpmtileview** (ErrorReport) - Report generation
- ✅ **fu** (FuseUtils) - Visual ID, QDF access
- ✅ **reqinfo** (RequestInfo) - Unit information
- ✅ **sv** (PythonSV) - Hardware access simulation
- ✅ **ipc** (IPC) - Inter-process communication
- ✅ **config** - Configuration settings

### Key Functions Tested
- ✅ `logger()` - Main logging function
- ✅ `visual_str()` - Visual ID retrieval
- ✅ `qdf_str()` - QDF string retrieval
- ✅ `getWW()` - Work week calculation
- ✅ `request_unit_info()` - Unit information
- ✅ `fuses()` - Fuse mask reading
- ✅ `powercycle()` - Power control
- ✅ `power_status()` - Power status check

## Common Use Cases

### Test Case 1: Basic Logger Call
```python
import mock_dpmChecks as dpm
result = dpm.logger(TestName='Test1', Testnumber=1)
```

### Test Case 2: Full Parameters
```python
result = dpm.logger(
    visual='QVRX12345678',
    qdf='L0_DMRAP_XCC',
    TestName='FullTest',
    Testnumber=2,
    dr_dump=True,
    chkmem=1,
    debug_mca=1,
    folder='C:\\temp\\logs',
    WW='48',
    Bucket='UNCORE',
    refresh=True
)
```

### Test Case 3: UI Mode
```python
result = dpm.logger(
    TestName='UITest',
    Testnumber=3,
    UI=True
)
```

### Test Case 4: Batch Testing
```python
tests = [
    {'TestName': 'Core', 'Testnumber': 1, 'Bucket': 'CORE'},
    {'TestName': 'Uncore', 'Testnumber': 2, 'Bucket': 'UNCORE'},
    {'TestName': 'Memory', 'Testnumber': 3, 'Bucket': 'MEMORY'}
]

for test in tests:
    result = dpm.logger(**test)
    print(f"Test {test['TestName']}: {result['status']}")
```

## Expected Output

When running tests, you'll see:
```
================================================================================
[MOCK] logger function called
================================================================================
[MOCK] gcm.svStatus called with refresh=False
[MOCK] visual_str called with socket=None, die=compute0
[MOCK] fu.get_visual_id called with socket=None, tile=compute0
[MOCK] qdf_str called
[MOCK] fu.get_qdf_str called with socket=socket0, die=cbb0.base
[MOCK] getWW called, returning WW48

[MOCK] Logger Parameters:
  Visual ID: QVRX12345678
  QDF: L0_DMRAP_XCC
  Test Name: Test1
  Test Number: 1
  Product: DMR
  WW: 48
  Bucket: UNCORE
  UI Mode: False
  Folder: C:\temp\mock_logs\

[MOCK] Running standard logger mode...
[MOCK] dpmtileview.run called
  Visual ID: QVRX12345678
  Test Number: 1
  Test Name: Test1
  ...

[MOCK] Logger execution successful!
[MOCK] Result: {'status': 'success', 'report_path': '...', 'errors_found': 2, 'mca_decoded': True}

================================================================================
[MOCK] logger function completed
================================================================================
```

## Verify Installation

Run this to verify everything is set up correctly:
```powershell
cd c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR
python -c "import mock_dpmChecks as dpm; print('Mock module loaded successfully'); print(f'Product: {dpm.config.SELECTED_PRODUCT}'); dpm.logger(TestName='VerifyTest', Testnumber=0)"
```

## Troubleshooting

### Issue: Module not found
**Solution**: Ensure you're in the correct directory or add to path:
```python
import sys
sys.path.insert(0, r'c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR')
```

### Issue: Import errors
**Solution**: Check that all files are in the DMR folder:
- mock_dpmChecks.py
- test_logger.py
- examples.py

### Issue: Tests fail
**Solution**: Run individual tests to isolate the issue:
```powershell
python -c "import test_logger; test_logger.test_logger_basic()"
```

## Next Steps

1. ✅ Run the test suite to verify functionality
2. ✅ Try the examples to understand usage
3. ✅ Integrate with your testing workflow
4. ✅ Customize mock responses in `mock_config.json`
5. ✅ Add your own test scenarios

## Configuration

Edit `mock_config.json` to customize:
- Default visual IDs
- Default QDF strings
- Mock unit configurations
- Test scenarios
- Expected results

## Integration with Real Code

To use these mocks with actual `dpmChecks.py`:

```python
import sys

# Add mock path first
sys.path.insert(0, r'c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR')

# Import and inject mocks
import mock_dpmChecks

# Replace modules
sys.modules['gcm'] = mock_dpmChecks.gcm
sys.modules['dpmlog'] = mock_dpmChecks.dpmlog
sys.modules['dpmtileview'] = mock_dpmChecks.dpmtileview

# Now you can import real dpmChecks with mocked dependencies
```

## Support

For issues or questions:
- Check README.md for detailed documentation
- Review examples.py for usage patterns
- Examine test_logger.py for test implementation details

## Summary

✅ **10 comprehensive tests** covering all logger functionality  
✅ **8 example scenarios** demonstrating common use cases  
✅ **Full mock environment** simulating all dependencies  
✅ **Easy to use** - just run `python test_logger.py`  
✅ **Well documented** - README, examples, and comments  
✅ **Configurable** - JSON config for customization  

Happy Testing! 🎉
