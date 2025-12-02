"""
Test script for dpmChecks logger function using mocks
Tests various scenarios and parameter combinations
Created: December 2, 2025
"""

import sys
import os

# Add the mock module to the path
mock_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mock_path)

# Import the mock module
import mock_dpmChecks as dpm


def test_logger_basic():
    """Test basic logger functionality with minimal parameters"""
    print("\n" + "="*100)
    print("TEST 1: Basic Logger Call")
    print("="*100)
    
    result = dpm.logger(
        TestName='BasicTest',
        Testnumber=1
    )
    
    print(f"\nTest 1 Result: {result}")
    assert result is not None, "Logger should return a result"
    print("✓ TEST 1 PASSED\n")


def test_logger_with_visual_qdf():
    """Test logger with explicit visual ID and QDF"""
    print("\n" + "="*100)
    print("TEST 2: Logger with Visual ID and QDF")
    print("="*100)
    
    result = dpm.logger(
        visual='QVRX98765432',
        qdf='L0_DMRAP_XCC',
        TestName='VisualTest',
        Testnumber=2
    )
    
    print(f"\nTest 2 Result: {result}")
    assert result is not None, "Logger should return a result"
    print("✓ TEST 2 PASSED\n")


def test_logger_full_parameters():
    """Test logger with all parameters specified"""
    print("\n" + "="*100)
    print("TEST 3: Logger with Full Parameters")
    print("="*100)
    
    result = dpm.logger(
        visual='QVRX11111111',
        qdf='L0_DMRAP_XCC',
        TestName='FullParametersTest',
        Testnumber=3,
        dr_dump=True,
        chkmem=1,
        debug_mca=1,
        folder='C:\\temp\\test_logs',
        WW='48',
        Bucket='UNCORE',
        UI=False,
        refresh=True,
        logging=None,
        upload_to_disk=False,
        upload_to_danta=False
    )
    
    print(f"\nTest 3 Result: {result}")
    assert result is not None, "Logger should return a result"
    assert result['status'] == 'success', "Logger should complete successfully"
    print("✓ TEST 3 PASSED\n")


def test_logger_ui_mode():
    """Test logger in UI mode"""
    print("\n" + "="*100)
    print("TEST 4: Logger in UI Mode")
    print("="*100)
    
    result = dpm.logger(
        visual='QVRX22222222',
        qdf='L0_DMRSP_MCC',
        TestName='UITest',
        Testnumber=4,
        UI=True,
        WW='48'
    )
    
    print(f"\nTest 4 Result: {result}")
    assert result is not None, "Logger should return a result"
    print("✓ TEST 4 PASSED\n")


def test_logger_with_refresh():
    """Test logger with refresh enabled"""
    print("\n" + "="*100)
    print("TEST 5: Logger with Refresh")
    print("="*100)
    
    result = dpm.logger(
        TestName='RefreshTest',
        Testnumber=5,
        refresh=True
    )
    
    print(f"\nTest 5 Result: {result}")
    assert result is not None, "Logger should return a result"
    print("✓ TEST 5 PASSED\n")


def test_logger_multiple_calls():
    """Test multiple sequential logger calls"""
    print("\n" + "="*100)
    print("TEST 6: Multiple Sequential Logger Calls")
    print("="*100)
    
    tests = [
        {'TestName': 'MultiTest1', 'Testnumber': 6, 'Bucket': 'CORE'},
        {'TestName': 'MultiTest2', 'Testnumber': 7, 'Bucket': 'MEMORY'},
        {'TestName': 'MultiTest3', 'Testnumber': 8, 'Bucket': 'UNCORE'},
    ]
    
    results = []
    for test in tests:
        print(f"\n--- Running {test['TestName']} ---")
        result = dpm.logger(**test)
        results.append(result)
        assert result is not None, f"Logger should return a result for {test['TestName']}"
    
    print(f"\nTest 6 Results: {len(results)} tests completed")
    assert len(results) == 3, "All three logger calls should complete"
    print("✓ TEST 6 PASSED\n")


def test_logger_default_values():
    """Test logger default value handling"""
    print("\n" + "="*100)
    print("TEST 7: Logger Default Values")
    print("="*100)
    
    # Test with empty strings to trigger default value logic
    result = dpm.logger(
        visual='',  # Should use visual_str()
        qdf='',     # Should use qdf_str()
        TestName='DefaultsTest',
        Testnumber=9,
        WW=''       # Should use getWW()
    )
    
    print(f"\nTest 7 Result: {result}")
    assert result is not None, "Logger should return a result"
    print("✓ TEST 7 PASSED\n")


def test_logger_error_scenarios():
    """Test logger with potential error scenarios"""
    print("\n" + "="*100)
    print("TEST 8: Logger Error Handling")
    print("="*100)
    
    # Test with unusual but valid parameters
    result = dpm.logger(
        TestName='ErrorTest',
        Testnumber=10,
        chkmem=99,      # Unusual value
        debug_mca=99,   # Unusual value
        dr_dump=False,
        folder=None     # Should use default
    )
    
    print(f"\nTest 8 Result: {result}")
    assert result is not None, "Logger should handle unusual parameters"
    print("✓ TEST 8 PASSED\n")


def test_helper_functions():
    """Test helper functions used by logger"""
    print("\n" + "="*100)
    print("TEST 9: Helper Functions")
    print("="*100)
    
    # Test visual_str
    print("\n--- Testing visual_str ---")
    visual = dpm.visual_str()
    assert visual != '', "visual_str should return a value"
    print(f"Visual ID: {visual}")
    
    # Test qdf_str
    print("\n--- Testing qdf_str ---")
    qdf = dpm.qdf_str()
    assert qdf != '', "qdf_str should return a value"
    print(f"QDF: {qdf}")
    
    # Test product_str
    print("\n--- Testing product_str ---")
    product = dpm.product_str()
    assert product == 'DMR', "product_str should return DMR"
    print(f"Product: {product}")
    
    # Test getWW
    print("\n--- Testing getWW ---")
    ww = dpm.getWW()
    assert ww > 0 and ww <= 53, "getWW should return a valid week number"
    print(f"Work Week: {ww}")
    
    # Test request_unit_info
    print("\n--- Testing request_unit_info ---")
    unit_info = dpm.request_unit_info()
    assert unit_info is not None, "request_unit_info should return data"
    print(f"Unit Info: {unit_info}")
    
    print("\n✓ TEST 9 PASSED\n")


def test_config_access():
    """Test configuration access"""
    print("\n" + "="*100)
    print("TEST 10: Configuration Access")
    print("="*100)
    
    # Test config object
    print(f"Selected Product: {dpm.config.SELECTED_PRODUCT}")
    assert dpm.config.SELECTED_PRODUCT == 'DMR', "Config should have DMR as product"
    
    print(f"Product Config: {dpm.config.PRODUCT_CONFIG}")
    assert dpm.config.PRODUCT_CONFIG == 'DMR', "Product config should be DMR"
    
    print(f"Product Variant: {dpm.config.PRODUCT_VARIANT}")
    print(f"Product Chop: {dpm.config.PRODUCT_CHOP}")
    print(f"Base Path: {dpm.config.BASE_PATH}")
    
    # Test config methods
    dpm.config.reload()
    print("Config reload successful")
    
    pf = dpm.config.get_functions()
    print(f"Product functions: {pf}")
    
    print("\n✓ TEST 10 PASSED\n")


def run_all_tests():
    """Run all test cases"""
    print("\n" + "#"*100)
    print("#" + " "*98 + "#")
    print("#" + " "*30 + "DPMCHECKS LOGGER MOCK TEST SUITE" + " "*35 + "#")
    print("#" + " "*98 + "#")
    print("#"*100 + "\n")
    
    tests = [
        ("Basic Logger Call", test_logger_basic),
        ("Logger with Visual ID and QDF", test_logger_with_visual_qdf),
        ("Logger with Full Parameters", test_logger_full_parameters),
        ("Logger in UI Mode", test_logger_ui_mode),
        ("Logger with Refresh", test_logger_with_refresh),
        ("Multiple Sequential Logger Calls", test_logger_multiple_calls),
        ("Logger Default Values", test_logger_default_values),
        ("Logger Error Handling", test_logger_error_scenarios),
        ("Helper Functions", test_helper_functions),
        ("Configuration Access", test_config_access),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"   Error: {e}\n")
            failed += 1
        except Exception as e:
            print(f"\n✗ TEST ERROR: {test_name}")
            print(f"   Exception: {e}\n")
            failed += 1
    
    # Summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED ⚠️\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
