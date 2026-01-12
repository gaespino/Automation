# Simple test to check MockTeraterm instance creation and method access
import sys
sys.path.insert(0, '.')

from DebugFramework import TestMocks

def test_mockteraterm_methods():
    """Test MockTeraterm instance creation and method access"""
    print("=== Testing MockTeraterm Method Access ===")
    
    try:
        # Create MockTeraterm instance
        print("1. Creating MockTeraterm instance...")
        tt = TestMocks.MockTeraterm(
            visual='TEST_VID',
            test='Test_Method_Access',
            content='dragon',
            DebugLog=lambda msg, level: print(f"[TT] {msg}")
        )
        print("   ✅ MockTeraterm instance created successfully")
        
        # Check if run method exists
        print("2. Checking run method...")
        if hasattr(tt, 'run'):
            print("   ✅ run method exists")
        else:
            print("   ❌ run method missing")
            
        # Check all methods
        print("3. Available methods:")
        methods = [method for method in dir(tt) if not method.startswith('_') and callable(getattr(tt, method))]
        for method in methods:
            print(f"   - {method}")
            
        # Try calling run method
        print("4. Testing run method call...")
        tt.run()
        print("   ✅ run method called successfully")
        
        # Try calling other methods
        print("5. Testing other methods...")
        tt.boot_start()
        print("   ✅ boot_start called successfully")
        
        tt.boot_end()
        print("   ✅ boot_end called successfully")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_serialconnection_teraterm():
    """Test SerialConnection.teraterm method"""
    print("\n=== Testing SerialConnection.teraterm ===")
    
    try:
        print("1. Creating teraterm via SerialConnection...")
        tt = TestMocks.MockSerialConnection.teraterm(
            visual='TEST_VID',
            test='Test_Serial_Access',
            content='dragon',
            vvar1='80064000',
            vvar2='0x1000000',
            vvar3='0x4000000',
            DebugLog=lambda msg, level: print(f"[SC] {msg}")
        )
        print("   ✅ SerialConnection.teraterm created instance successfully")
        
        # Check type
        print(f"   Instance type: {type(tt)}")
        
        # Check if run method exists
        if hasattr(tt, 'run'):
            print("   ✅ run method exists on SerialConnection teraterm instance")
            # Try calling it
            tt.run()
            print("   ✅ run method called successfully")
        else:
            print("   ❌ run method missing on SerialConnection teraterm instance")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mockteraterm_methods()
    test_serialconnection_teraterm()