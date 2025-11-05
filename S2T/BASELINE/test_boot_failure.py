#!/usr/bin/env python3
"""
Test boot failure scenarios - ensure no test content when boot fails
"""
import sys
import os

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import mocks first
from DebugFramework import TestMocks
TestMocks.setup_all_mocks()

def test_boot_failure_scenarios():
    """Test that boot failures result in minimal logs with no test content"""
    
    print("=== Testing Boot Failure Scenarios ===")
    
    # Test Dragon boot failure
    print("\n1. Testing Dragon Boot Failure:")
    dragon_mock = TestMocks.MockTeraterm(
        content="dragon",
        test="DragonBootFailTest",
        execution_state=None
    )
    
    # Force boot failure
    dragon_mock._boot_reached = False
    dragon_mock._bios_postcode = "0xaf0000ff"
    dragon_mock._test_failed = True
    
    # Generate log
    log_content = dragon_mock._generate_boot_failure_log("dragon")
    print(f"Dragon boot failure log length: {len(log_content)} characters")
    print("Dragon boot failure log preview:")
    print(log_content[:300] + "..." if len(log_content) > 300 else log_content)
    
    # Verify no test content
    assert "MerlinX.efi" not in log_content, "Boot failure log should not contain test execution"
    assert f"POST Code: {dragon_mock._bios_postcode}" in log_content, "Should show failure postcode"
    assert "BOOT FAILED" in log_content, "Should indicate boot failure"
    assert "No Dragon test content executed" in log_content, "Should indicate no test execution"
    print("✓ Dragon boot failure correctly shows no test content")
    
    # Test Linux boot failure  
    print("\n2. Testing Linux Boot Failure:")
    linux_mock = TestMocks.MockTeraterm(
        content="linux_tsl", 
        test="LinuxBootFailTest",
        execution_state=None
    )
    
    # Force boot failure
    linux_mock._boot_reached = False
    linux_mock._bios_postcode = "0x4f000000"
    linux_mock._test_failed = True
    
    # Generate log
    log_content = linux_mock._generate_boot_failure_log("linux")
    print(f"Linux boot failure log length: {len(log_content)} characters")
    print("Linux boot failure log preview:")
    print(log_content[:300] + "..." if len(log_content) > 300 else log_content)
    
    # Verify no test content
    assert "TSL" not in log_content, "Boot failure log should not contain TSL content"
    assert f"POST Code: {linux_mock._bios_postcode}" in log_content, "Should show failure postcode"
    assert "BOOT FAILED" in log_content, "Should indicate boot failure"
    assert "No test content executed" in log_content, "Should indicate no test execution"
    print("✓ Linux boot failure correctly shows no test content")
    
    # Test successful boot with test content
    print("\n3. Testing Successful Boot with Test Content:")
    success_mock = TestMocks.MockTeraterm(
        content="dragon",
        test="DragonSuccessTest", 
        execution_state=None
    )
    
    # Force boot success
    success_mock._boot_reached = True
    success_mock._test_failed = False
    
    # Generate full log 
    log_content = success_mock._generate_dragon_log()
    print(f"Dragon success log length: {len(log_content)} characters")
    print("Dragon success log preview:")
    print(log_content[:400] + "..." if len(log_content) > 400 else log_content)
    
    # Verify test content present
    assert "POST Code: 0xef0000ff - EFI Boot successful" in log_content, "Success log should show successful boot"
    assert "MerlinX.efi" in log_content, "Success log should contain test execution"
    assert "Entering Dragon test execution" in log_content, "Should indicate test execution started"
    print("✓ Dragon success correctly shows full test content")
    
    print("\n=== All Boot Failure Tests Passed ===")

def test_framework_integration_with_boot_failures():
    """Test framework integration with boot failure scenarios"""
    
    print("\n=== Testing Framework Integration with Boot Failures ===")
    
    # Test multiple iterations with some boot failures
    for i in range(5):
        print(f"\nTesting iteration {i+1}:")
        
        mock = TestMocks.MockTeraterm(
            content="dragon" if i % 2 == 0 else "linux_tsl",
            test=f"BootTest_{i+1}",
            execution_state=None
        )
        
        # Simulate the full execution process
        mock.run()  # This will call _generate_realistic_log() which includes boot success check
        
        print(f"  Result: {mock.testresult}")
        print(f"  Postcode: {mock.scratchpad}")
        print(f"  Boot reached: {getattr(mock, '_boot_reached', 'Unknown')}")
        
        # Check that capture.log was created
        capture_log = r'C:\Temp\capture.log'
        if os.path.exists(capture_log):
            with open(capture_log, 'r') as f:
                content = f.read()
            print(f"  Capture log size: {len(content)} characters")
            
            # Check consistency
            if "BOOT FAILED" in content:
                assert "FAIL" in mock.testresult, "Boot failure should result in FAIL test result"
                assert mock.scratchpad not in ["0xef0000ff", "0x58000000"], "Boot failure should not have success postcodes"
                print("  ✓ Boot failure correctly reflected in test result and postcode")
            else:
                # Should have test content if not boot failure
                if mock.scratchpad in ["0xef0000ff", "0x58000000"]:
                    print("  ✓ Successful boot has appropriate content")
    
    print("\n=== Framework Integration Tests Passed ===")

if __name__ == "__main__":
    test_boot_failure_scenarios()
    test_framework_integration_with_boot_failures()
    print("\n🎉 All tests passed! Boot failure logic working correctly.")