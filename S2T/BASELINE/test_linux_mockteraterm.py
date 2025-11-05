# Test Linux MockTeraterm functionality
import sys
sys.path.insert(0, '.')

from DebugFramework import TestMocks

def test_linux_mockteraterm():
    """Test MockTeraterm with Linux content"""
    print("=== Testing Linux MockTeraterm ===")
    
    try:
        # Test Linux content
        print("1. Testing Linux Dragon content...")
        tt_linux = TestMocks.MockTeraterm(
            visual='TEST_LINUX',
            test='Linux_Dragon_Test',
            content='Linux',  # Linux content type
            DebugLog=lambda msg, level: print(f"[LINUX TT] {msg}")
        )
        
        tt_linux.run()
        print(f"   Result: {tt_linux.testresult}")
        print(f"   Scratchpad (BIOS Postcode): {tt_linux.scratchpad}")
        
        print("\n2. Testing regular Dragon content...")
        tt_dragon = TestMocks.MockTeraterm(
            visual='TEST_DRAGON',
            test='Dragon_Test', 
            content='Dragon',  # Dragon content type
            DebugLog=lambda msg, level: print(f"[DRAGON TT] {msg}")
        )
        
        tt_dragon.run()
        print(f"   Result: {tt_dragon.testresult}")
        print(f"   Scratchpad (BIOS Postcode): {tt_dragon.scratchpad}")
        
        print("\n3. Testing TSL Linux generation...")
        # Generate multiple tests to see variety
        for i in range(3):
            tt = TestMocks.MockTeraterm(
                visual=f'TSL_TEST_{i}',
                test=f'TSL_Test_{i}',
                content='Linux',
                DebugLog=lambda msg, level: None  # Silent
            )
            tt.run()
            postcode = tt.scratchpad
            status = "PASS" if "PASS" in tt.testresult else "FAIL"
            print(f"   Test {i}: {status} - Postcode: {postcode}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_linux_mockteraterm()