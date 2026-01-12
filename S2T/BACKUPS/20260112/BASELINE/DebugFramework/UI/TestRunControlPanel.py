#!/usr/bin/env python3
"""
Test runner script that handles all the mocking and setup
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch


current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.append(parent_dir)

def setup_mocks():
    """Set up all necessary mocks before importing anything"""
    
    # Mock all problematic user modules
    mock_modules = [
        'users',
        'users.framework',
        'users.framework.Framework',
        'users.framework.s2t',
        'users.framework.dpm',
        'users.framework.ser',
        'users.framework.fh',
        'users.framework.gcm',
        'users.framework.FrameworkUtils',
    ]
    
    for module in mock_modules:
        sys.modules[module] = Mock()
    
    # Mock specific functions that might be imported directly
    sys.modules['users.framework.s2t'].SELECTED_PRODUCT = "MockProduct"
    sys.modules['users.framework.dpm'].qdf_str = Mock(return_value="MockQDF")
    sys.modules['users.framework.dpm'].getWW = Mock(return_value="2024WW01")

def run_tests():
    """Run the test suite"""
    
    # Set up mocks first
    setup_mocks()
    
    # Add current directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # Import test modules after mocking
    try:
        from UI.TestControlPanel import TestControlPanelSafe, TestMockFramework
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add tests
        suite.addTests(loader.loadTestsFromTestCase(TestControlPanelSafe))
        suite.addTests(loader.loadTestsFromTestCase(TestMockFramework))
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=2,
            stream=sys.stdout,
            descriptions=True,
            failfast=False
        )
        
        result = runner.run(suite)
        
        # Print detailed summary
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        
        if result.testsRun > 0:
            success_count = result.testsRun - len(result.failures) - len(result.errors)
            success_rate = (success_count / result.testsRun) * 100
            print(f"Success rate: {success_rate:.1f}% ({success_count}/{result.testsRun})")
        
        # Print failures and errors
        if result.failures:
            print(f"\nFAILURES ({len(result.failures)}):")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print(f"\nERRORS ({len(result.errors)}):")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
        
        print(f"{'='*60}")
        
        # Return exit code
        return 0 if result.wasSuccessful() else 1
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all required modules are available")
        return 1
    except Exception as e:
        print(f"Test execution error: {e}")
        return 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)