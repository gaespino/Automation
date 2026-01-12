# Quick test of the enhanced Dragon log generation
import sys
import os
sys.path.insert(0, '.')

# Import the TestMocks
from DebugFramework import TestMocks
import tempfile

def test_dragon_log_formats():
    """Test the new Dragon log formats for both passing and failing cases"""
    print("=== Testing Enhanced Dragon Log Generation ===")
    
    # Test multiple log generations to see both passing and failing formats
    for i in range(5):
        print(f"\n--- Test {i+1} ---")
        
        # Generate a test log
        test_log = os.path.join(tempfile.gettempdir(), f"dragon_test_{i}.log")
        TestMocks.MockFileHandler._create_mock_dragon_log(test_log)
        
        # Read and show the first part of the log to see the format
        if os.path.exists(test_log):
            with open(test_log, 'r') as f:
                content = f.read()
                
            # Determine if it's a passing or failing test
            if "TEST STATUS: PASSED" in content:
                test_type = "PASSING"
            elif "TEST STATUS: FAILED" in content:
                test_type = "FAILING"
            else:
                test_type = "UNKNOWN"
                
            print(f"Generated {test_type} Dragon test")
            
            # Show key parts of the log
            lines = content.split('\n')
            
            # Show seed lines
            for line in lines[:10]:
                if "Running FS1:" in line and ".obj" in line:
                    # Extract seed from the line
                    seed_part = line.split('\\')[-1]
                    print(f"  Seed found: {seed_part}")
            
            # Show status
            for line in lines:
                if "TEST STATUS:" in line:
                    print(f"  Status: {line.strip()}")
                    break
            
            print(f"  Log saved to: {test_log}")
            
            # Extract seed using the FileHandler
            try:
                seed = TestMocks.MockFileHandler.extract_fail_seed(test_log)
                print(f"  Extracted seed: {seed}")
            except Exception as e:
                print(f"  Seed extraction error: {e}")
        else:
            print("  ERROR: Log file not created")

if __name__ == "__main__":
    test_dragon_log_formats()