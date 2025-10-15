# Test Framework integration with enhanced mocks
import sys
import os
import tempfile
sys.path.insert(0, '.')

# Import the enhanced TestMocks
from DebugFramework import TestMocks

def test_framework_integration():
    """Test the enhanced Mock system with proper Framework workflow"""
    print("=== Testing Framework Integration with TTL configs.ini ===")
    
    # Create experiment and TTL folders
    experiment_folder = os.path.join(tempfile.gettempdir(), "framework_test_experiment")
    ttl_folder = os.path.join(tempfile.gettempdir(), "framework_ttl")
    os.makedirs(experiment_folder, exist_ok=True)
    os.makedirs(ttl_folder, exist_ok=True)
    
    print(f"Experiment folder: {experiment_folder}")
    print(f"TTL folder: {ttl_folder}")
    
    # Simulate Framework experiment parameters (what Framework passes to SerialConnection)
    framework_params = {
        'visual': 'MOCK_VID_789',
        'qdf': 'MOCK_QDF_GNR',
        'bucket': 'GNR_Bucket_A',
        'tfolder': experiment_folder,
        'ttl_folder': ttl_folder,   # TTL folder where configs.ini goes
        'test': 'Dragon_Framework_Test',
        'content': 'dragon',
        'vvar1': '80067890',      # Framework experiment variable 1
        'vvar2': '0x1200000',    # Framework experiment variable 2  
        'vvar3': '0x5000000',    # Framework experiment variable 3
        'PassString': ['Test Passed'],
        'FailString': ['Test Failed', 'FAILED'],
        'DebugLog': lambda msg, level: print(f"[FRAMEWORK DEBUG] {msg}")
    }
    
    print(f"\nFramework Experiment Data:")
    print(f"  Visual ID: {framework_params['visual']}")
    print(f"  Test: {framework_params['test']}")
    print(f"  Framework VVARs: 1={framework_params['vvar1']}, 2={framework_params['vvar2']}, 3={framework_params['vvar3']}")
    
    # Simulate multiple experiment iterations (as Framework would do)
    for iteration in range(1, 3):
        print(f"\n--- Framework Experiment Iteration {iteration} ---")
        
        # Framework: Create Teraterm instance (this creates configs.ini in TTL folder)
        print(f"  1. Framework creates TTL configs.ini with experiment data")
        tt_instance = TestMocks.MockSerialConnection.teraterm(**framework_params)
        
        # Framework: Execute test (TTL macro reads configs.ini and generates logs)
        print(f"  2. TTL macro reads configs.ini and executes test")
        tt_instance.boot_start()
        tt_instance.boot_end()  # This generates the log with VVARs from configs.ini
        
        # Framework: SerialConnection collects the log
        print(f"  3. SerialConnection collects generated log")
        collected_log = TestMocks.MockSerialConnection.collect_teraterm_log(
            tt_instance, experiment_folder, iteration
        )
        
        if collected_log and os.path.exists(collected_log):
            print(f"  ✅ Generated log: {os.path.basename(collected_log)}")
            
            # Test seed extraction from the collected log
            seed = TestMocks.MockFileHandler.extract_fail_seed(
                collected_log, 
                PassString=['Test Passed'], 
                FailString=['Test Failed', 'FAILED']
            )
            print(f"  ✅ Extracted seed: {seed}")
            
            # Verify the log contains the correct VVARs from configs.ini
            with open(collected_log, 'r') as f:
                content = f.read()
                
            # Check for Framework VVARs (the specific values we set)
            if 'Value="80067890"' in content and 'Value="0x1200000"' in content and 'Value="0x5000000"' in content:
                print(f"  ✅ Framework VVARs from configs.ini found in log")
            else:
                print(f"  ❌ Framework VVARs missing in log")
                
            # Check for failure indicators  
            if 'Number="0xC"' in content and 'Number="0x20"' in content:
                print(f"  ✅ Failure indicators (0xC-0x20) found in log")
            else:
                print(f"  ❌ Failure indicators missing in log")
                
        else:
            print(f"  ❌ Failed to generate/collect log for iteration {iteration}")
    
    # Show the generated configs.ini
    config_path = os.path.join(ttl_folder, 'configs.ini')
    if os.path.exists(config_path):
        print(f"\n=== Generated configs.ini (TTL folder) ===")
        with open(config_path, 'r') as f:
            config_content = f.read()
            print(config_content)
    else:
        print(f"\n❌ configs.ini not found at: {config_path}")
    
    print(f"\n=== Experiment Folder Contents ===")
    if os.path.exists(experiment_folder):
        files = os.listdir(experiment_folder)
        for file in files:
            print(f"  {file}")
    else:
        print("  No files generated")

if __name__ == "__main__":
    test_framework_integration()