"""
S2T Testing Mock System
Extends HardwareMocks.py to enable comprehensive S2T function testing
Mocks only external dependencies not available in the S2T folder
"""

import sys
import os
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import threading

# Import base hardware mocks
try:
    from HardwareMocks import get_mock_sv, get_mock_ipc, setup_hardware_mocks, MockSV, MockIPC
except ImportError:
    print("[S2T MOCKS] Warning: HardwareMocks not available, creating minimal fallback")
    MockSV = None
    MockIPC = None

class MockToolextBoot:
    """Mock for toolext.bootscript.boot module"""
    
    def __init__(self):
        self.current_state = "idle"
        self.break_points = []
        self.fuse_overrides = {}
        
    def go(self, gotil=None, fused_unit=True, enable_strap_checks=False, 
           compute_config=None, enable_pm=True, segment="GNR", **kwargs):
        """Mock b.go() - bootscript execution"""
        print(f"[MOCK TOOLEXT] b.go() called with:")
        print(f"  gotil: {gotil}")
        print(f"  fused_unit: {fused_unit}")
        print(f"  enable_strap_checks: {enable_strap_checks}")
        print(f"  compute_config: {compute_config}")
        print(f"  enable_pm: {enable_pm}")
        print(f"  segment: {segment}")
        
        # Simulate boot stages
        boot_stages = [
            ("Phase 1: Reset", 1.0),
            ("Phase 2: Microcode Load", 2.0),
            ("Phase 3: Fuse Override", 1.5),
            ("Phase 4: Memory Init", 3.0),
            ("Phase 5: CPU Init", 2.5),
            ("Phase 6: Boot Complete", 1.0)
        ]
        
        for stage, duration in boot_stages:
            print(f"[MOCK TOOLEXT] {stage}...")
            time.sleep(duration * 0.1)  # Shortened for testing
            
        self.current_state = "booted"
        print(f"[MOCK TOOLEXT] Boot sequence completed successfully")
        
    def cont(self, curr_state=None, **kwargs):
        """Mock b.cont() - continue from break point"""
        print(f"[MOCK TOOLEXT] b.cont() called from state: {curr_state}")
        time.sleep(0.5)
        self.current_state = curr_state or "continued"
        
    def reset(self, **kwargs):
        """Mock b.reset() - reset system"""
        print(f"[MOCK TOOLEXT] b.reset() called")
        self.current_state = "reset"
        time.sleep(1.0)
        
    def break_on(self, break_point, **kwargs):
        """Mock setting break points"""
        print(f"[MOCK TOOLEXT] Setting break point: {break_point}")
        self.break_points.append(break_point)

class MockFuseUtility:
    """Mock for toolext.bootscript.toolbox.fuse_utility module"""
    
    def __init__(self):
        self.mock_visual_ids = {
            'compute0': 'MOCK74GC556700043',
            'compute1': 'MOCK74GC556700044', 
            'compute2': 'MOCK74GC556700045'
        }
        self.mock_qdf_data = {
            'compute0': 'MOCK_QDF_GNR_B0_001',
            'compute1': 'MOCK_QDF_GNR_B0_002',
            'compute2': 'MOCK_QDF_GNR_B0_003'
        }
    
    def get_visual_id(self, socket=None, tile=None, **kwargs):
        """Mock fu.get_visual_id()"""
        tile_key = tile if tile else 'compute0'
        vid = self.mock_visual_ids.get(tile_key, f'MOCK_VID_{tile_key.upper()}')
        print(f"[MOCK FUSE_UTIL] get_visual_id({tile}) = {vid}")
        return vid
    
    def get_qdf_str(self, socket=None, die=None, **kwargs):
        """Mock fu.get_qdf_str()"""
        die_key = die if die else 'compute0'
        qdf = self.mock_qdf_data.get(die_key, f'MOCK_QDF_{die_key.upper()}')
        print(f"[MOCK FUSE_UTIL] get_qdf_str({die}) = {qdf}")
        return qdf
    
    def get_ult(self, socket=None, tile=None, ult_in=None, **kwargs):
        """Mock fu.get_ult() - Unit Level Traceability"""
        return {
            'textStr': f'MOCK_ULT_{tile or "compute0"}',
            'socket': socket or 0,
            'tile': tile or 'compute0'
        }

class MockUSBPowerSplitter:
    """Mock USB Power Splitter for power control"""
    
    def __init__(self):
        self.power_state = "ON"
        self.channels = {f"CH{i}": True for i in range(8)}
        
    def power_on(self, channel=None):
        """Mock power on"""
        if channel:
            self.channels[channel] = True
            print(f"[MOCK USB_PWR] Channel {channel} powered ON")
        else:
            self.power_state = "ON"
            print(f"[MOCK USB_PWR] All channels powered ON")
            
    def power_off(self, channel=None):
        """Mock power off"""
        if channel:
            self.channels[channel] = False
            print(f"[MOCK USB_PWR] Channel {channel} powered OFF")
        else:
            self.power_state = "OFF"
            print(f"[MOCK USB_PWR] All channels powered OFF")
            
    def get_status(self):
        """Get power status"""
        return {
            'main_power': self.power_state,
            'channels': self.channels.copy()
        }

class MockUSBPowerSplitterModule:
    """Mock for the USB Power Splitter module"""
    
    def __init__(self):
        pass
        
    def USBPowerSplitter(self):
        return MockUSBPowerSplitter()

class MockGraniterapidsModule:
    """Mock for graniterapids product-specific modules"""
    
    def __init__(self):
        self.toolext = MockGraniterapidsToolext()
        
class MockGraniterapidsToolext:
    """Mock for graniterapids.toolext hierarchy"""
    
    def __init__(self):
        self.bootscript = MockGraniterapidsBootscript()
        
class MockGraniterapidsBootscript:
    """Mock for graniterapids.toolext.bootscript hierarchy"""
    
    def __init__(self):
        self.toolbox = MockGraniterapidsToolbox()
        
class MockGraniterapidsToolbox:
    """Mock for graniterapids.toolext.bootscript.toolbox hierarchy"""
    
    def __init__(self):
        self.ult_module = MockUltModule()

class MockUltModule:
    """Mock for Unit Level Traceability module"""
    
    def get_ult_info(self, **kwargs):
        """Mock ULT information retrieval"""
        return {
            'unit_id': 'MOCK_UNIT_12345',
            'lot_code': 'MOCK_LOT_ABC123',
            'wafer_id': 'MOCK_WAFER_W01',
            'die_x': random.randint(0, 20),
            'die_y': random.randint(0, 15)
        }

class MockBitData:
    """Mock for ipccli.BitData class"""
    
    def __init__(self, value=0, width=32):
        self.value = value
        self.width = width
        
    def __int__(self):
        return self.value
        
    def __str__(self):
        return f"0x{self.value:x}"

def setup_s2t_mocks(product: str = "GNR"):
    """
    Setup comprehensive S2T mocking system
    Mocks external dependencies while allowing real S2T code to run
    """
    import sys
    import types
    
    print(f"[S2T MOCKS] Setting up S2T testing environment for {product}...")
    
    # Setup base hardware mocks first
    if MockSV and MockIPC:
        setup_hardware_mocks(product)
    else:
        print("[S2T MOCKS] Using minimal hardware mocking")
    
    # Create toolext module hierarchy
    toolext = types.ModuleType('toolext')
    toolext.bootscript = types.ModuleType('toolext.bootscript')
    toolext.bootscript.boot = MockToolextBoot()
    toolext.bootscript.toolbox = types.ModuleType('toolext.bootscript.toolbox')
    toolext.bootscript.toolbox.fuse_utility = MockFuseUtility()
    toolext.bootscript.toolbox.power_control = types.ModuleType('toolext.bootscript.toolbox.power_control')
    toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl = MockUSBPowerSplitterModule()
    
    # Create graniterapids module hierarchy
    graniterapids = MockGraniterapidsModule()
    
    # Register all modules in sys.modules
    sys.modules['toolext'] = toolext
    sys.modules['toolext.bootscript'] = toolext.bootscript
    sys.modules['toolext.bootscript.boot'] = toolext.bootscript.boot
    sys.modules['toolext.bootscript.toolbox'] = toolext.bootscript.toolbox
    sys.modules['toolext.bootscript.toolbox.fuse_utility'] = toolext.bootscript.toolbox.fuse_utility
    sys.modules['toolext.bootscript.toolbox.power_control'] = toolext.bootscript.toolbox.power_control
    sys.modules['toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl'] = toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl
    
    sys.modules['graniterapids'] = graniterapids
    sys.modules['graniterapids.toolext'] = graniterapids.toolext
    sys.modules['graniterapids.toolext.bootscript'] = graniterapids.toolext.bootscript
    sys.modules['graniterapids.toolext.bootscript.toolbox'] = graniterapids.toolext.bootscript.toolbox
    sys.modules['graniterapids.toolext.bootscript.toolbox.ult_module'] = graniterapids.toolext.bootscript.toolbox.ult_module
    
    # Mock ipccli.BitData if not already mocked
    if 'ipccli' in sys.modules and hasattr(sys.modules['ipccli'], 'BitData'):
        # Already mocked by HardwareMocks
        pass
    else:
        # Add BitData to existing mock or create minimal ipccli
        import ipccli
        if hasattr(ipccli, '__dict__'):
            ipccli.BitData = MockBitData
        else:
            # Create minimal ipccli mock
            class MinimalIPCCLI:
                BitData = MockBitData
                def baseaccess(self):
                    return get_mock_ipc() if MockIPC else object()
            sys.modules['ipccli'] = MinimalIPCCLI()
    
    print("[S2T MOCKS] S2T testing environment setup completed")
    print("[S2T MOCKS] Available mocked modules:")
    print("  - toolext.bootscript.boot (b.go, b.cont, b.reset)")
    print("  - toolext.bootscript.toolbox.fuse_utility (fu.get_visual_id, fu.get_qdf_str)")
    print("  - toolext.bootscript.toolbox.power_control.USBPowerSplitterFullControl")
    print("  - graniterapids.toolext.bootscript.toolbox.ult_module")
    print("  - ipccli.BitData")
    
    return True

def test_s2t_functions(product: str = "GNR"):
    """
    Test S2T functions in isolated environment
    This allows testing S2T capabilities without Framework UI
    """
    
    print(f"\n{'='*60}")
    print(f"TESTING S2T FUNCTIONS DIRECTLY - PRODUCT: {product}")
    print(f"{'='*60}")
    
    try:
        # Setup S2T mocks
        setup_s2t_mocks(product)
        
        print("\n1. Testing CoreManipulation functions...")
        
        # Import S2T modules (they should work with mocks)
        import S2T.CoreManipulation as cm
        import S2T.dpmChecks as dpm
        import S2T.ConfigsLoader as cl
        
        print("   ✓ S2T modules imported successfully")
        
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
            fuses = dpm.fuses(rdFuses=True, printFuse=True)
            print(f"   ✓ Fuse data retrieved: {len(fuses) if fuses else 0} entries")
        except Exception as e:
            print(f"   ⚠ Fuse operations failed: {e}")
        
        # Test configuration loading
        print("\n5. Testing configuration loading...")
        try:
            # Test config loading (should work with real JSON files)
            print(f"   ✓ Selected product: {cl.SELECTED_PRODUCT}")
            print(f"   ✓ Product config: {cl.PRODUCT_CONFIG}")
            print(f"   ✓ Product variant: {cl.PRODUCT_VARIANT}")
        except Exception as e:
            print(f"   ⚠ Configuration loading failed: {e}")
        
        # Test bootscript mock
        print("\n6. Testing bootscript functionality...")
        try:
            import toolext.bootscript.boot as b
            print("   ✓ Bootscript module imported")
            
            # Test boot sequence
            b.go(segment=product, enable_pm=True)
            print("   ✓ Boot sequence test completed")
        except Exception as e:
            print(f"   ⚠ Bootscript test failed: {e}")
        
        print(f"\n{'='*60}")
        print("S2T FUNCTION TESTING COMPLETED")
        print("You can now use S2T functions directly for testing:")
        print("  import S2T.CoreManipulation as cm")
        print("  import S2T.dpmChecks as dpm") 
        print("  import S2T.SetTesterRegs as s2t")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ S2T Function Testing Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test the S2T mock system
    test_products = ["GNR", "CWF", "DMR"]
    
    for product in test_products:
        print(f"\n{'='*80}")
        print(f"TESTING S2T MOCKS FOR PRODUCT: {product}")
        print(f"{'='*80}")
        
        success = test_s2t_functions(product)
        if success:
            print(f"✅ {product} S2T testing environment ready")
        else:
            print(f"❌ {product} S2T testing environment failed")