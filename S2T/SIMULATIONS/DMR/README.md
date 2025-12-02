# DPMChecks Logger Function Mock Tests - DMR Product

This directory contains mock simulations for testing the `logger` function from `dpmChecks.py` in the BASELINE_DMR directory.

## Files

### `mock_dpmChecks.py`
Comprehensive mock module that simulates all dependencies required by the `logger` function:

- **MockConfig**: Simulates configuration settings for DMR product
- **MockGCM**: Mocks CoreManipulation module (gcm) functions
- **MockDPMLog**: Mocks Logger UI module (dpmlog)
- **MockDPMTileView**: Mocks ErrorReport module (dpmtileview)
- **MockFuseUtils**: Mocks fuse utility functions (fu)
- **MockRequestInfo**: Mocks unit information requests
- **MockSV**: Mocks pythonsv namednodes.sv module
- **MockIPC**: Mocks IPC/baseaccess functionality

### `test_logger.py`
Comprehensive test suite for the logger function with 10 test cases:

1. **Basic Logger Call**: Tests minimal parameter usage
2. **Logger with Visual ID and QDF**: Tests explicit ID/QDF parameters
3. **Logger with Full Parameters**: Tests all parameters specified
4. **Logger in UI Mode**: Tests UI mode functionality
5. **Logger with Refresh**: Tests refresh parameter
6. **Multiple Sequential Logger Calls**: Tests consecutive calls
7. **Logger Default Values**: Tests default value handling
8. **Logger Error Handling**: Tests unusual parameter scenarios
9. **Helper Functions**: Tests visual_str, qdf_str, getWW, etc.
10. **Configuration Access**: Tests config object functionality

## Usage

### Run All Tests
```powershell
cd c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR
python test_logger.py
```

### Run Individual Test
```python
import sys
sys.path.insert(0, r'c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR')
import mock_dpmChecks as dpm

# Test basic logger call
result = dpm.logger(TestName='MyTest', Testnumber=1)
print(result)
```

### Interactive Testing
```python
# In Python console
import sys
sys.path.insert(0, r'c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR')
import mock_dpmChecks as dpm

# Test logger with different scenarios
dpm.logger(TestName='Test1', Testnumber=1)
dpm.logger(visual='QVRX12345', qdf='L0_DMRAP_XCC', TestName='Test2', Testnumber=2)
dpm.logger(TestName='Test3', Testnumber=3, UI=True)

# Test helper functions
visual = dpm.visual_str()
qdf = dpm.qdf_str()
ww = dpm.getWW()
unit_info = dpm.request_unit_info()
```

## Mock Behavior

The mock module simulates realistic behavior:

- **Visual IDs**: Returns mock visual IDs (e.g., "QVRX12345678")
- **QDF Strings**: Returns mock QDF strings (e.g., "L0_DMRAP_XCC")
- **Work Weeks**: Returns current ISO calendar work week
- **Error Reports**: Simulates successful report generation with metadata
- **Status Checks**: Simulates system status checks and refresh operations
- **Print Output**: All mock functions print their calls for debugging

## Test Results

Expected output when all tests pass:
```
################################################################################
#                                                                              #
#                     DPMCHECKS LOGGER MOCK TEST SUITE                         #
#                                                                              #
################################################################################

TEST 1: Basic Logger Call
...
✓ TEST 1 PASSED

TEST 2: Logger with Visual ID and QDF
...
✓ TEST 2 PASSED

...

==============================================================================
TEST SUMMARY
==============================================================================
Total Tests: 10
Passed: 10
Failed: 0

🎉 ALL TESTS PASSED! 🎉
```

## Logger Function Parameters

The mock logger function supports all original parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| visual | str | '' | Unit Visual ID |
| qdf | str | '' | QDF string |
| TestName | str | '' | Name of the test |
| Testnumber | int | 0 | Test number |
| dr_dump | bool | True | Enable DR dump |
| chkmem | int | 0 | Memory check flag |
| debug_mca | int | 0 | MCA debug flag |
| folder | str | None | Output folder path |
| WW | str | '' | Work week |
| Bucket | str | 'UNCORE' | Test bucket category |
| UI | bool | False | Enable UI mode |
| refresh | bool | False | Refresh status before run |
| logging | object | None | Logger object |
| upload_to_disk | bool | False | Upload results to disk |
| upload_to_danta | bool | False | Upload results to Danta |

## Integration with Real dpmChecks

To test the real `dpmChecks.py` module with these mocks:

```python
import sys
sys.path.insert(0, r'c:\Git\Automation\Automation\S2T\SIMULATIONS\DMR')

# Import mocks
import mock_dpmChecks

# Replace real modules with mocks in dpmChecks
import sys
sys.modules['gcm'] = mock_dpmChecks.gcm
sys.modules['dpmlog'] = mock_dpmChecks.dpmlog
sys.modules['dpmtileview'] = mock_dpmChecks.dpmtileview

# Now import and test real dpmChecks
# (Note: Full integration requires additional setup)
```

## Notes

- All mock functions print their execution for visibility
- Mock results simulate successful operations
- Error handling is included to test exception paths
- Configuration is set for DMR product by default
- Can be adapted for other products (GNR, CWF) by modifying MockConfig

## Future Enhancements

Potential improvements:
- Add configurable mock responses
- Simulate error conditions
- Add performance metrics
- Create mock data files
- Add network simulation for upload operations
- Support for multiple socket configurations
