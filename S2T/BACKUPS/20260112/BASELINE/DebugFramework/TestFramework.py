# test_launcher.py - Import mocks first, then run tests

# CRITICAL: Import mock_setup FIRST to setup all mocks
import TestMocks

def run_control_panel_test(product: str = "GNR"):
    """Run the control panel with test environment"""
    
    try:
        print("\n" + "="*60)
        print("STARTING CONTROL PANEL IN TEST MODE")
        print(f"PRODUCT: {product}")
        print("="*60)
        print("NOTE: All S2T operations and file uploads are mocked")
        print("You can safely test all framework functionality")
        print("="*60 + "\n")
        
        # Setup mocks with product specification
        TestMocks.setup_all_mocks(product)
        
        # Now we can safely import SystemDebug
        print("Importing SystemDebug with mocked dependencies...")
        import SystemDebug as gdf

        # Run control panel
        gdf.ControlPanel()
        
    except Exception as e:
        print(f"Control panel test error: {e}")
        import traceback
        traceback.print_exc()

def run_automation_panel_test(product: str = "GNR"):
    """Run the automation panel with test environment"""
    
    try:
        print("\n" + "="*60)
        print("STARTING AUTOMATION PANEL IN TEST MODE")
        print(f"PRODUCT: {product}")
        print("="*60)
        print("NOTE: All S2T operations and file uploads are mocked")
        print("You can safely test all framework functionality")
        print("="*60 + "\n")
        
        # Setup mocks with product specification
        TestMocks.setup_all_mocks(product)
        
        # Now we can safely import SystemDebug
        print("Importing SystemDebug with mocked dependencies...")
        import SystemDebug as gdf

        # Run automation panel
        gdf.AutomationPanel()
        
    except Exception as e:
        print(f"Automation panel test error: {e}")
        import traceback
        traceback.print_exc()

def run_test_scenario(scenario_name="basic_loop"):
    """Run a specific test scenario"""
    
    try:
        print("Importing SystemDebug with mocked dependencies...")
        import SystemDebug as gdf
        
        # Create framework instance with database upload disabled
        framework = gdf.Framework(upload_to_database=False)
        
        # Get test scenario
        scenarios = {
            'basic_loop': get_basic_loop_test(),
            'freq_sweep': get_frequency_sweep_test(),
            'volt_sweep': get_voltage_sweep_test()
        }
        
        test_data = scenarios.get(scenario_name)
        if not test_data:
            print(f"Unknown scenario: {scenario_name}")
            return
        
        print(f"\n{'='*60}")
        print(f"RUNNING TEST SCENARIO: {scenario_name.upper()}")
        print(f"{'='*60}")
        
        # Execute the test
        results = framework.RecipeExecutor(
            data=test_data,
            experiment_name=f"Mock_{scenario_name}_Test"
        )
        
        print(f"\n{'='*60}")
        print(f"TEST SCENARIO COMPLETED: {scenario_name.upper()}")
        print(f"Results: {results}")
        print(f"{'='*60}")
        
        return results
        
    except Exception as e:
        print(f"Test execution error: {e}")
        import traceback
        traceback.print_exc()

def get_basic_loop_test():
    """Basic loop test configuration"""
    return {
        'Test Name': 'Mock_Loop_Test',
        'Test Type': 'Loops',
        'Loops': 5,
        'Test Mode': 'mesh',
        'Content': 'dragon',
        'Visual ID': 'MOCK123',
        'QDF': 'MockQDF',
        'Bucket': 'MockBucket',
        'Core Frequency': 2400,
        'Mesh Frequency': 1800,
        'Core Voltage': 1.0,
        'Mesh Voltage': 0.9,
        'Voltage Type': 'nom',
        'Reset': True,
        'Reset on Pass': False,
        'Mask': 'System',
        'Pass String': 'PASS,SUCCESS',
        'Fail String': 'FAIL,ERROR,TIMEOUT',
        'Experiment': 'Enabled'
    }

def get_frequency_sweep_test():
    """Frequency sweep test configuration"""
    return {
        'Test Name': 'Mock_Freq_Sweep',
        'Test Type': 'Sweep',
        'Type': 'frequency',
        'Domain': 'ia',
        'Start': 2000,
        'End': 2800,
        'Steps': 200,
        'Test Mode': 'mesh',
        'Content': 'dragon',
        'Visual ID': 'MOCK123',
        'QDF': 'MockQDF',
        'Bucket': 'MockBucket',
        'Mesh Frequency': 1800,
        'Voltage Type': 'nom',
        'Reset': True,
        'Reset on Pass': False,
        'Mask': 'System',
        'Pass String': 'PASS,SUCCESS',
        'Fail String': 'FAIL,ERROR,TIMEOUT',
        'Experiment': 'Enabled'
    }

def get_voltage_sweep_test():
    """Voltage sweep test configuration"""
    return {
        'Test Name': 'Mock_Volt_Sweep',
        'Test Type': 'Sweep',
        'Type': 'voltage',
        'Domain': 'ia',
        'Start': 0.8,
        'End': 1.2,
        'Steps': 0.1,
        'Test Mode': 'mesh',
        'Content': 'dragon',
        'Visual ID': 'MOCK123',
        'QDF': 'MockQDF',
        'Bucket': 'MockBucket',
        'Core Frequency': 2400,
        'Mesh Frequency': 1800,
        'Voltage Type': 'override',
        'Reset': True,
        'Reset on Pass': False,
        'Mask': 'System',
        'Pass String': 'PASS,SUCCESS',
        'Fail String': 'FAIL,ERROR,TIMEOUT',
        'Experiment': 'Enabled'
    }

def main():
    """Main test launcher"""
    
    print("Debug Framework Test Launcher")
    print("=" * 50)
    print("All mocks have been applied successfully!")
    
    while True:
        print("\nAvailable tests:")
        print("1. Basic Loop Test (5 iterations)")
        print("2. Frequency Sweep Test")
        print("3. Voltage Sweep Test")
        print("4. Control Panel Test Mode")
        print("5. All Scenarios")
        print("0. Exit")
        
        choice = input("\nSelect test (0-5): ").strip()
        
        if choice == '0':
            print("Exiting test launcher...")
            break
            
        elif choice == '1':
            print("\nRunning Basic Loop Test...")
            run_test_scenario('basic_loop')
            
        elif choice == '2':
            print("\nRunning Frequency Sweep Test...")
            run_test_scenario('freq_sweep')
            
        elif choice == '3':
            print("\nRunning Voltage Sweep Test...")
            run_test_scenario('volt_sweep')
            
        elif choice == '4':
            print("\nStarting Control Panel in Test Mode...")
            run_control_panel_test()
            
        elif choice == '5':
            print("\nRunning All Test Scenarios...")
            scenarios = ['basic_loop', 'freq_sweep', 'volt_sweep']
            for scenario in scenarios:
                print(f"\n{'-'*40}")
                print(f"Running {scenario}...")
                print(f"{'-'*40}")
                run_test_scenario(scenario)
                input("Press Enter to continue to next test...")
        
        else:
            print("Invalid choice. Please try again.")

def run_s2t_function_test(product: str = "GNR"):
    """Run S2T functions directly for testing without Framework UI"""
    
    try:
        print("\n" + "="*60)
        print("STARTING S2T FUNCTION TESTING MODE")
        print(f"PRODUCT: {product}")
        print("="*60)
        print("NOTE: Testing S2T capabilities directly")
        print("All hardware operations are mocked for safe testing")
        print("="*60 + "\n")
        
        # Import and run S2T test framework
        import S2TTestFramework
        
        success = S2TTestFramework.test_s2t_functions_directly(product)
        
        if success:
            print("✅ S2T function testing completed successfully!")
            print("You can now use S2T functions directly:")
            print("  - CoreManipulation functions")
            print("  - dpmChecks operations") 
            print("  - Register read/write")
            print("  - Boot sequence testing")
        else:
            print("❌ S2T function testing failed!")
            
        return success
        
    except Exception as e:
        print(f"S2T function test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Choose your testing mode:
    
    # 1. Test Framework UI (Automation Panel)
    #run_automation_panel_test("GNR")
    
    # 2. Test Framework UI (Control Panel)
    #run_control_panel_test("GNR") 
    
    # 3. Test S2T Functions Directly (NEW!)
    run_s2t_function_test("GNR")
    
    print(f"\n{'='*60}")
    print("AVAILABLE TESTING MODES:")
    print("1. run_control_panel_test(product)    - Framework Control Panel UI")
    print("2. run_automation_panel_test(product) - Framework Automation Panel UI")  
    print("3. run_s2t_function_test(product)     - Direct S2T Function Testing")
    print("4. main()                             - Interactive test menu")
    print(f"{'='*60}")