"""
Quick example scripts for using dpmChecks logger mocks
Run these examples to see the mock behavior
"""

import sys
import os

# Add mock path
mock_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, mock_path)

import mock_dpmChecks as dpm


def example_1_basic():
    """Example 1: Basic logger call"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Logger Call")
    print("="*80)
    
    result = dpm.logger(
        TestName='BasicExample',
        Testnumber=1
    )
    
    print(f"\nResult: {result}")


def example_2_custom_visual():
    """Example 2: Logger with custom visual ID and QDF"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Custom Visual ID and QDF")
    print("="*80)
    
    result = dpm.logger(
        visual='QVRX87654321',
        qdf='L0_DMRAP_XCC',
        TestName='CustomVisualTest',
        Testnumber=2,
        Bucket='MEMORY'
    )
    
    print(f"\nResult: {result}")


def example_3_debug_mode():
    """Example 3: Logger with debug options enabled"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Debug Mode with MCA and Memory Check")
    print("="*80)
    
    result = dpm.logger(
        TestName='DebugTest',
        Testnumber=3,
        debug_mca=1,
        chkmem=1,
        dr_dump=True,
        folder='C:\\temp\\debug_logs'
    )
    
    print(f"\nResult: {result}")


def example_4_ui_mode():
    """Example 4: Logger in UI mode"""
    print("\n" + "="*80)
    print("EXAMPLE 4: UI Mode")
    print("="*80)
    
    result = dpm.logger(
        TestName='UIExample',
        Testnumber=4,
        UI=True
    )
    
    print(f"\nResult: {result}")


def example_5_batch_tests():
    """Example 5: Running multiple tests in sequence"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Batch Test Execution")
    print("="*80)
    
    test_configs = [
        {
            'TestName': 'CoreTest',
            'Testnumber': 5,
            'Bucket': 'CORE',
            'chkmem': 0
        },
        {
            'TestName': 'UncoreTest',
            'Testnumber': 6,
            'Bucket': 'UNCORE',
            'debug_mca': 1
        },
        {
            'TestName': 'MemoryTest',
            'Testnumber': 7,
            'Bucket': 'MEMORY',
            'chkmem': 1
        }
    ]
    
    results = []
    for config in test_configs:
        print(f"\n--- Running {config['TestName']} ---")
        result = dpm.logger(**config)
        results.append(result)
    
    print(f"\n\nBatch Complete: {len(results)} tests executed")
    return results


def example_6_helper_functions():
    """Example 6: Using helper functions"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Helper Functions")
    print("="*80)
    
    # Get unit information
    print("\n--- Unit Information ---")
    visual = dpm.visual_str()
    qdf = dpm.qdf_str()
    product = dpm.product_str()
    ww = dpm.getWW()
    
    print(f"Visual ID: {visual}")
    print(f"QDF: {qdf}")
    print(f"Product: {product}")
    print(f"Work Week: {ww}")
    
    # Get complete unit info
    print("\n--- Complete Unit Info ---")
    unit_info = dpm.request_unit_info()
    for key, value in unit_info.items():
        print(f"  {key}: {value}")
    
    # Check fuses
    print("\n--- Fuse Information ---")
    fuse_data = dpm.fuses(rdFuses=True, printFuse=False)
    for fuse_name, fuse_value in fuse_data.items():
        print(f"  {fuse_name}: {hex(fuse_value)}")


def example_7_power_control():
    """Example 7: Power control functions"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Power Control Functions")
    print("="*80)
    
    # Check power status
    print("\n--- Power Status ---")
    status = dpm.power_status()
    print(f"Power Status: {status}")
    
    # Simulate power cycle
    print("\n--- Power Cycle Simulation ---")
    dpm.powercycle(stime=5, ports=[1, 2])


def example_8_config_inspection():
    """Example 8: Inspecting configuration"""
    print("\n" + "="*80)
    print("EXAMPLE 8: Configuration Inspection")
    print("="*80)
    
    print(f"Selected Product: {dpm.config.SELECTED_PRODUCT}")
    print(f"Product Config: {dpm.config.PRODUCT_CONFIG}")
    print(f"Product Variant: {dpm.config.PRODUCT_VARIANT}")
    print(f"Product Chop: {dpm.config.PRODUCT_CHOP}")
    print(f"Base Path: {dpm.config.BASE_PATH}")
    print(f"Max Physical: {dpm.config.MAXPHYSICAL}")
    print(f"Fuse Instance: {dpm.config.FUSE_INSTANCE}")
    
    print("\nBootscript Data:")
    for key, value in dpm.config.BOOTSCRIPT_DATA['DMR'].items():
        print(f"  {key}: {value}")


def run_all_examples():
    """Run all examples"""
    print("\n" + "#"*80)
    print("#  DPMChecks Logger Mock - Usage Examples")
    print("#"*80 + "\n")
    
    examples = [
        example_1_basic,
        example_2_custom_visual,
        example_3_debug_mode,
        example_4_ui_mode,
        example_5_batch_tests,
        example_6_helper_functions,
        example_7_power_control,
        example_8_config_inspection
    ]
    
    for example in examples:
        try:
            example()
            input("\nPress Enter to continue to next example...")
        except KeyboardInterrupt:
            print("\n\nExamples interrupted by user.")
            break
        except Exception as e:
            print(f"\nError in example: {e}")
            input("\nPress Enter to continue...")
    
    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run dpmChecks logger mock examples')
    parser.add_argument('--all', action='store_true', help='Run all examples')
    parser.add_argument('--example', type=int, choices=range(1, 9), 
                       help='Run specific example (1-8)')
    
    args = parser.parse_args()
    
    if args.example:
        examples = {
            1: example_1_basic,
            2: example_2_custom_visual,
            3: example_3_debug_mode,
            4: example_4_ui_mode,
            5: example_5_batch_tests,
            6: example_6_helper_functions,
            7: example_7_power_control,
            8: example_8_config_inspection
        }
        examples[args.example]()
    elif args.all:
        run_all_examples()
    else:
        # Show menu
        print("\nDPMChecks Logger Mock Examples")
        print("="*80)
        print("1. Basic Logger Call")
        print("2. Custom Visual ID and QDF")
        print("3. Debug Mode with MCA and Memory Check")
        print("4. UI Mode")
        print("5. Batch Test Execution")
        print("6. Helper Functions")
        print("7. Power Control Functions")
        print("8. Configuration Inspection")
        print("9. Run All Examples")
        print("0. Exit")
        print("="*80)
        
        choice = input("\nSelect an example (0-9): ").strip()
        
        if choice == '9':
            run_all_examples()
        elif choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
            examples = {
                '1': example_1_basic,
                '2': example_2_custom_visual,
                '3': example_3_debug_mode,
                '4': example_4_ui_mode,
                '5': example_5_batch_tests,
                '6': example_6_helper_functions,
                '7': example_7_power_control,
                '8': example_8_config_inspection
            }
            examples[choice]()
        elif choice == '0':
            print("Exiting...")
        else:
            print("Invalid choice")
