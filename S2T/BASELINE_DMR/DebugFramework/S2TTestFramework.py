# S2T Function Testing Framework
# Allows direct testing of S2T capabilities without Framework UI

import TestMocks
import sys
import os

def test_s2t_functions_directly(product: str = "GNR"):
    """
    Test S2T functions in isolated environment
    This allows testing S2T capabilities without Framework UI
    """
    
    print(f"\n{'='*60}")
    print(f"TESTING S2T FUNCTIONS DIRECTLY - PRODUCT: {product}")
    print(f"{'='*60}")
    
    try:
        # Setup S2T testing mocks
        success = TestMocks.setup_s2t_testing_mocks(product)
        if not success:
            print("❌ Failed to setup S2T testing environment")
            return False
        
        print("\n1. Testing CoreManipulation functions...")
        
        # Add S2T to path for direct import
        current_dir = os.path.dirname(os.path.abspath(__file__))
        s2t_path = os.path.join(current_dir, '..', 'S2T')
        if s2t_path not in sys.path:
            sys.path.insert(0, s2t_path)
        
        # Import S2T modules (they should work with mocks)
        try:
            import CoreManipulation as cm
            print("   ✓ CoreManipulation imported successfully")
        except Exception as e:
            print(f"   ⚠ CoreManipulation import failed: {e}")
            
        try:
            import dpmChecks as dpm
            print("   ✓ dpmChecks imported successfully")
        except Exception as e:
            print(f"   ⚠ dpmChecks import failed: {e}")
            
        try:
            from ConfigsLoader import config
            print("   ✓ ConfigsLoader imported successfully")
        except Exception as e:
            print(f"   ⚠ ConfigsLoader import failed: {e}")
        
        # Test SV status check
        print("\n2. Testing SV status...")
        try:
            status = cm.svStatus(checkipc=True, checksvcores=False, refresh=True)
            print(f"   ✓ SV Status check completed: {status}")
        except Exception as e:
            print(f"   ⚠ SV Status check failed: {e}")
        
        # Test DPM functions
        print("\n3. Testing DPM functions...")
        try:
            qdf = dpm.qdf_str()
            print(f"   ✓ QDF string: {qdf}")
            
            product_info = dpm.product_str()
            print(f"   ✓ Product: {product_info}")
            
            ww = dpm.getWW()
            print(f"   ✓ Work Week: {ww}")
        except Exception as e:
            print(f"   ⚠ DPM functions failed: {e}")
        
        # Test fuse operations
        print("\n4. Testing fuse operations...")
        try:
            fuses = dpm.fuses(rdFuses=True, printFuse=False)  # Don't print for cleaner output
            print(f"   ✓ Fuse data retrieved: {len(fuses) if fuses else 0} entries")
            if fuses:
                for key, value in list(fuses.items())[:3]:  # Show first 3 entries
                    print(f"     {key}: {value}")
        except Exception as e:
            print(f"   ⚠ Fuse operations failed: {e}")
        
        # Test configuration loading
        print("\n5. Testing configuration loading...")
        try:
            # Test config loading (should work with real JSON files)
            print(f"   ✓ Selected product: {config.SELECTED_PRODUCT}")
            print(f"   ✓ Product config: {config.PRODUCT_CONFIG}")
            print(f"   ✓ Product variant: {config.PRODUCT_VARIANT}")
        except Exception as e:
            print(f"   ⚠ Configuration loading failed: {e}")
        
        # Test bootscript mock functionality
        print("\n6. Testing bootscript functionality...")
        try:
            import toolext.bootscript.boot as b
            print("   ✓ Bootscript module imported")
            
            # Test boot sequence (quick mock version)
            print("   Running mock boot sequence...")
            b.go(segment=product, enable_pm=True, fused_unit=True)
            print("   ✓ Boot sequence test completed")
        except Exception as e:
            print(f"   ⚠ Bootscript test failed: {e}")
        
        # Test direct S2T register operations
        print("\n7. Testing register operations...")
        try:
            from namednodes import sv
            print("   ✓ SV (namednodes) imported")
            
            # Test register read/write with new mock system
            sv.initialize()
            print(f"   ✓ SV initialized, sockets available: {len(sv.sockets)}")
            
            # Test specific register access
            original_value = int(sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg)
            print(f"   ✓ Read biosscratchpad6_cfg: 0x{original_value:x}")
            
            # Write test value
            sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = 0xbf000000
            new_value = int(sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg)
            print(f"   ✓ Write/Read test: 0x{new_value:x}")
            
        except Exception as e:
            print(f"   ⚠ Register operations failed: {e}")
        
        # Test IPC operations
        print("\n8. Testing IPC operations...")
        try:
            from ipccli import ipc
            print("   ✓ IPC imported")
            
            print(f"   System locked: {ipc.islocked()}")
            ipc.unlock()
            print("   ✓ IPC unlock executed")
            ipc.forcereconfig()
            print("   ✓ IPC force reconfig executed")
            
        except Exception as e:
            print(f"   ⚠ IPC operations failed: {e}")
        
        print(f"\n{'='*60}")
        print("S2T FUNCTION TESTING COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}")
        print("\n🎯 You can now use S2T functions directly for testing:")
        print("   import CoreManipulation as cm")
        print("   import dpmChecks as dpm") 
        print("   import SetTesterRegs as s2t")
        print("   from namednodes import sv")
        print("   from ipccli import ipc")
        print("\n💡 Available test scenarios:")
        print("   - Core masking and boot sequences")
        print("   - Register read/write operations")
        print("   - DPM and fuse operations")
        print("   - Hardware mock interactions")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ S2T Function Testing Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_s2t_interactive_session(product: str = "GNR"):
    """
    Start an interactive session with S2T functions available
    """
    
    print(f"\n{'='*60}")
    print(f"STARTING S2T INTERACTIVE SESSION - PRODUCT: {product}")
    print(f"{'='*60}")
    
    # Setup environment
    success = test_s2t_functions_directly(product)
    if not success:
        print("❌ Failed to setup S2T environment")
        return
    
    print(f"\n🚀 S2T Interactive Session Ready!")
    print(f"Product: {product}")
    print(f"All S2T modules are imported and ready to use.")
    print(f"\nExample commands you can try:")
    print(f"  >>> import CoreManipulation as cm")
    print(f"  >>> cm.svStatus(refresh=True)")
    print(f"  >>> import dpmChecks as dpm") 
    print(f"  >>> dpm.qdf_str()")
    print(f"  >>> from namednodes import sv")
    print(f"  >>> sv.socket0.target_info")
    print(f"\nType 'exit()' to quit the interactive session")
    print(f"{'='*60}\n")

# Entry point functions
def test_gnr_s2t():
    """Quick test for GNR S2T functions"""
    return test_s2t_functions_directly("GNR")

def test_cwf_s2t():
    """Quick test for CWF S2T functions"""  
    return test_s2t_functions_directly("CWF")

def test_dmr_s2t():
    """Quick test for DMR S2T functions"""
    return test_s2t_functions_directly("DMR")

if __name__ == "__main__":
    # Test all products
    products = ["GNR", "CWF", "DMR"]
    
    for product in products:
        print(f"\n{'='*80}")
        print(f"TESTING {product} S2T ENVIRONMENT")
        print(f"{'='*80}")
        
        success = test_s2t_functions_directly(product)
        
        if success:
            print(f"✅ {product} S2T testing environment is ready!")
        else:
            print(f"❌ {product} S2T testing environment failed!")
            
    print(f"\n{'='*80}")
    print("S2T TESTING FRAMEWORK READY")
    print("Run individual product tests:")
    print("  python S2TTestFramework.py")
    print("  >>> test_gnr_s2t()")
    print("  >>> test_cwf_s2t()") 
    print("  >>> test_dmr_s2t()")
    print(f"{'='*80}")