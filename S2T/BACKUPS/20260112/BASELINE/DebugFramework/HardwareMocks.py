"""
Hardware Register Mocking System for S2T Framework
Provides comprehensive mocking for ipccli and namednodes (sv) registers
Extensible design for multiple products (GNR, CWF, DMR)
"""

import time
import threading
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field

class RegisterType(Enum):
    """Types of registers for different access patterns"""
    READ_WRITE = "rw"
    READ_ONLY = "ro"
    WRITE_ONLY = "wo"
    FUSE = "fuse"
    CONFIG = "config"

@dataclass
class RegisterInfo:
    """Information about a hardware register"""
    name: str
    value: int = 0
    reg_type: RegisterType = RegisterType.READ_WRITE
    bit_width: int = 32
    description: str = ""
    reset_value: int = 0

class MockRegisterMap:
    """Thread-safe register map with product-specific configurations"""
    
    def __init__(self, product: str = "GNR"):
        self.product = product
        self._registers: Dict[str, RegisterInfo] = {}
        self._lock = threading.RLock()
        self._access_log: List[Dict[str, Any]] = []
        self._initialized = False
        
        # Load product-specific registers
        self._load_registers()
    
    def _load_registers(self):
        """Load registers for the specified product"""
        registers = REGISTER_MAPS.get(self.product, REGISTER_MAPS["GNR"])
        
        with self._lock:
            for path, reg_info in registers.items():
                self._registers[path] = RegisterInfo(**reg_info)
            self._initialized = True
    
    def read(self, register_path: str) -> int:
        """Read register value with logging"""
        with self._lock:
            if register_path not in self._registers:
                # Auto-create missing registers for flexibility
                self._registers[register_path] = RegisterInfo(
                    name=register_path.split('.')[-1],
                    value=0,
                    description=f"Auto-created register for {register_path}"
                )
            
            reg = self._registers[register_path]
            self._log_access("READ", register_path, reg.value)
            
            # Simulate hardware access delay
            time.sleep(0.001)
            return reg.value
    
    def write(self, register_path: str, value: int) -> bool:
        """Write register value with validation"""
        with self._lock:
            if register_path not in self._registers:
                # Auto-create for flexibility
                self._registers[register_path] = RegisterInfo(
                    name=register_path.split('.')[-1],
                    value=value,
                    description=f"Auto-created register for {register_path}"
                )
                return True
            
            reg = self._registers[register_path]
            
            # Validate register type
            if reg.reg_type == RegisterType.READ_ONLY:
                self._log_access("WRITE_FAILED", register_path, value, "Read-only register")
                return False
            
            # Validate bit width
            max_value = (1 << reg.bit_width) - 1
            if value > max_value:
                self._log_access("WRITE_FAILED", register_path, value, f"Value exceeds {reg.bit_width}-bit limit")
                return False
            
            old_value = reg.value
            reg.value = value
            self._log_access("WRITE", register_path, value, f"Previous: 0x{old_value:x}")
            
            # Simulate hardware access delay
            time.sleep(0.002)
            return True
    
    def _log_access(self, operation: str, path: str, value: int, note: str = ""):
        """Log register access for debugging"""
        log_entry = {
            "timestamp": time.time(),
            "operation": operation,
            "register": path,
            "value": f"0x{value:x}",
            "note": note
        }
        self._access_log.append(log_entry)
        
        # Keep log size manageable
        if len(self._access_log) > 1000:
            self._access_log = self._access_log[-500:]
    
    def get_access_log(self) -> List[Dict[str, Any]]:
        """Get register access history"""
        with self._lock:
            return self._access_log.copy()
    
    def reset_registers(self):
        """Reset all registers to their reset values"""
        with self._lock:
            for reg in self._registers.values():
                reg.value = reg.reset_value
            self._access_log.clear()

class MockSVNode:
    """Mock SV (namednodes) hierarchy node"""
    
    def __init__(self, name: str, register_map: MockRegisterMap, parent_path: str = ""):
        self.name = name
        self._register_map = register_map
        self._parent_path = parent_path
        self._children: Dict[str, 'MockSVNode'] = {}
        self._attributes: Dict[str, Any] = {}
        
        # Build full path
        if parent_path:
            self.full_path = f"{parent_path}.{name}"
        else:
            self.full_path = name
    
    def __getattr__(self, attr_name: str):
        """Dynamic attribute access for register hierarchy"""
        
        # Check for cached children first
        if attr_name in self._children:
            return self._children[attr_name]
        
        # Check for cached attributes
        if attr_name in self._attributes:
            return self._attributes[attr_name]
        
        # Try to create child node
        child_path = f"{self.full_path}.{attr_name}"
        
        # Check if this could be a register endpoint
        if self._is_register_endpoint(child_path):
            return MockRegister(child_path, self._register_map)
        
        # Create child node
        child_node = MockSVNode(attr_name, self._register_map, self.full_path)
        self._children[attr_name] = child_node
        return child_node
    
    def __setattr__(self, attr_name: str, value):
        """Handle register writes"""
        if attr_name.startswith('_') or attr_name in ['name', 'full_path']:
            super().__setattr__(attr_name, value)
            return
        
        # Handle register write
        if hasattr(self, '_register_map'):
            reg_path = f"{self.full_path}.{attr_name}"
            if isinstance(value, int):
                self._register_map.write(reg_path, value)
                return
        
        super().__setattr__(attr_name, value)
    
    def _is_register_endpoint(self, path: str) -> bool:
        """Check if path represents a register endpoint"""
        # Common register endpoint patterns
        register_patterns = [
            'cfg', 'disable', 'enable', 'mask', 'counter', 'status',
            'biosscratchpad', 'core_disable', 'fused_ia_core',
            'vp2intersect_dis', 'ip_disable_fuses'
        ]
        
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in register_patterns)

class MockRegister:
    """Mock register endpoint that supports read/write operations"""
    
    def __init__(self, path: str, register_map: MockRegisterMap):
        self.path = path
        self._register_map = register_map
    
    def __int__(self):
        """Support int() conversion for register reads"""
        return self._register_map.read(self.path)
    
    def __index__(self):
        """Support use in numeric contexts"""
        return self._register_map.read(self.path)
    
    def __eq__(self, other):
        """Support equality comparison"""
        if isinstance(other, int):
            return self._register_map.read(self.path) == other
        return False
    
    def show(self):
        """Mock the .show() method common in SV"""
        value = self._register_map.read(self.path)
        print(f"[MOCK] {self.path} = 0x{value:x} ({value})")

class MockSV:
    """Mock SV (namednodes) interface"""
    
    def __init__(self, product: str = "GNR"):
        self._register_map = MockRegisterMap(product)
        self._sockets: List[MockSVNode] = []
        self._initialized = False
    
    def initialize(self):
        """Mock sv.initialize()"""
        print("[MOCK SV] Initializing SV interface...")
        self._initialized = True
        
        # Create socket hierarchy
        self.socket0 = MockSVNode("socket0", self._register_map)
        self._sockets = [self.socket0]
        
        # Pre-populate common structures
        self._setup_socket_structure()
    
    def refresh(self):
        """Mock sv.refresh()"""
        print("[MOCK SV] Refreshing SV registers...")
        # Simulate refresh delay
        time.sleep(0.1)
    
    @property
    def sockets(self):
        """Mock sv.sockets property"""
        return self._sockets
    
    def get_by_path(self, path: str):
        """Mock sv.get_by_path()"""
        # Navigate through the path
        parts = path.split('.')
        current = self
        
        for part in parts:
            current = getattr(current, part)
        
        return current
    
    def _setup_socket_structure(self):
        """Set up common socket structure"""
        # Set up target_info
        self.socket0._attributes['target_info'] = {
            'segment': 'GNR' if self._register_map.product == 'GNR' else self._register_map.product,
            'chop': 'GNR_B0',
            'variant': 'ES1',
            'instance': 0
        }
        
        # Pre-create common nodes
        computes_node = MockSVNode("computes", self._register_map, "socket0")
        computes_node._attributes['name'] = ['compute0', 'compute1'] 
        computes_node._attributes['instance'] = [0, 1]
        self.socket0._children['computes'] = computes_node
        
        ios_node = MockSVNode("ios", self._register_map, "socket0")
        ios_node._attributes['name'] = ['io0']
        self.socket0._children['ios'] = ios_node

class MockIPC:
    """Mock IPC (ipccli) interface"""
    
    def __init__(self):
        self._locked = False
        self._target_reset = False
        self._running = False
    
    def resettarget(self):
        """Mock ipc.resettarget()"""
        print("[MOCK IPC] Reset target")
        self._target_reset = True
        self._running = False
        time.sleep(0.5)  # Simulate reset time
    
    def unlock(self):
        """Mock ipc.unlock()"""
        print("[MOCK IPC] Unlock")
        self._locked = False
    
    def forcereconfig(self):
        """Mock ipc.forcereconfig()"""
        print("[MOCK IPC] Force reconfiguration")
        time.sleep(0.2)
    
    def go(self):
        """Mock ipc.go()"""
        print("[MOCK IPC] Go (continue execution)")
        self._running = True
    
    def islocked(self) -> bool:
        """Mock ipc.islocked()"""
        return self._locked
    
    def reconnect(self):
        """Mock ipc.reconnect()"""
        print("[MOCK IPC] Reconnecting...")
        time.sleep(1.0)
    
    @property
    def uncores(self):
        """Mock ipc.uncores property"""
        return MockIPCUncores()

class MockIPCUncores:
    """Mock IPC uncores interface"""
    
    def unlock(self):
        """Mock ipc.uncores.unlock()"""
        print("[MOCK IPC] Uncore unlock")

# Product-specific register maps based on JSON configurations
REGISTER_MAPS = {
    "GNR": {
        # Socket configuration registers
        "socket0.target_info.segment": {"name": "segment", "value": 0x474E52, "reg_type": RegisterType.READ_ONLY},  # 'GNR'
        "socket0.target_info.chop": {"name": "chop", "value": 0x474E52, "reg_type": RegisterType.READ_ONLY},
        "socket0.target_info.variant": {"name": "variant", "value": 0x455331, "reg_type": RegisterType.READ_ONLY},  # 'ES1'
        
        # Boot control registers
        "socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg": {
            "name": "biosscratchpad6_cfg", "value": 0x0, "reset_value": 0x0,
            "description": "BIOS scratchpad for boot control"
        },
        
        # Core disable masks
        "socket0.pcudata.fused_ia_core_disable_0": {
            "name": "fused_ia_core_disable_0", "value": 0x0, "reg_type": RegisterType.READ_ONLY,
            "description": "Fused IA core disable mask lower 32 bits"
        },
        "socket0.pcudata.fused_ia_core_disable_1": {
            "name": "fused_ia_core_disable_1", "value": 0x0, "reg_type": RegisterType.READ_ONLY,
            "description": "Fused IA core disable mask upper 32 bits"
        },
        
        # Fuse registers (example for compute0)
        "socket0.compute0.fuses.hwrs_top_rom.ip_disable_fuses_dword6_core_disable": {
            "name": "core_disable_fuse", "value": 0x0, "reg_type": RegisterType.FUSE,
            "description": "Core disable fuse register"
        },
        
        # PCU SST (Speed Select Technology) fuse registers
        "socket0.compute0.fuses.pcu.pcode_sst_pp_0_core_disable_mask": {
            "name": "sst_pp0_core_mask", "value": 0x0, "reg_type": RegisterType.FUSE,
            "description": "SST Performance Profile 0 core disable mask"
        },
        "socket0.compute0.fuses.pcu.pcode_sst_pp_1_core_disable_mask": {
            "name": "sst_pp1_core_mask", "value": 0x0, "reg_type": RegisterType.FUSE,
            "description": "SST Performance Profile 1 core disable mask"
        },
        "socket0.compute0.fuses.pcu.pcode_sst_pp_2_core_disable_mask": {
            "name": "sst_pp2_core_mask", "value": 0x0, "reg_type": RegisterType.FUSE,
            "description": "SST Performance Profile 2 core disable mask"
        },
        "socket0.compute0.fuses.pcu.pcode_sst_pp_3_core_disable_mask": {
            "name": "sst_pp3_core_mask", "value": 0x0, "reg_type": RegisterType.FUSE,
            "description": "SST Performance Profile 3 core disable mask"
        },
        
        # Frequency ratio fuses - CFC (Core/Fabric/Cache)
        "socket0.computes.fuses.pcu.pcode_sst_pp_0_cfc_p0_ratio": {
            "name": "cfc_p0_ratio_pp0", "value": 0x18, "reg_type": RegisterType.FUSE,
            "description": "CFC P0 ratio for SST PP0"
        },
        "socket0.computes.fuses.pcu.pcode_sst_pp_0_cfc_p1_ratio": {
            "name": "cfc_p1_ratio_pp0", "value": 0x10, "reg_type": RegisterType.FUSE,
            "description": "CFC P1 ratio for SST PP0"
        },
        "socket0.computes.fuses.pcu.pcode_cfc_pn_ratio": {
            "name": "cfc_pn_ratio", "value": 0x08, "reg_type": RegisterType.FUSE,
            "description": "CFC Pn (minimum) ratio"
        },
        "socket0.computes.fuses.pcu.pcode_cfc_min_ratio": {
            "name": "cfc_min_ratio", "value": 0x08, "reg_type": RegisterType.FUSE,
            "description": "CFC minimum operating ratio"
        },
        
        # IA (Intel Architecture) core frequency ratios
        "socket0.computes.fuses.pcu.pcode_ia_p0_ratio": {
            "name": "ia_p0_ratio", "value": 0x20, "reg_type": RegisterType.FUSE,
            "description": "IA core P0 (maximum) frequency ratio"
        },
        "socket0.computes.fuses.pcu.pcode_ia_pn_ratio": {
            "name": "ia_pn_ratio", "value": 0x08, "reg_type": RegisterType.FUSE,
            "description": "IA core Pn (minimum) frequency ratio"
        },
        "socket0.computes.fuses.pcu.pcode_ia_min_ratio": {
            "name": "ia_min_ratio", "value": 0x08, "reg_type": RegisterType.FUSE,
            "description": "IA core minimum operating ratio"
        },
        
        # AVX instruction set ratios per SST profile
        "socket0.computes.fuses.pcu.pcode_sst_pp_0_avx2_p1_ratio": {
            "name": "avx2_p1_ratio_pp0", "value": 0x18, "reg_type": RegisterType.FUSE,
            "description": "AVX2 P1 ratio for SST PP0"
        },
        "socket0.computes.fuses.pcu.pcode_sst_pp_0_avx512_p1_ratio": {
            "name": "avx512_p1_ratio_pp0", "value": 0x15, "reg_type": RegisterType.FUSE,
            "description": "AVX512 P1 ratio for SST PP0"
        },
        "socket0.computes.fuses.pcu.pcode_sst_pp_0_sse_p1_ratio": {
            "name": "sse_p1_ratio_pp0", "value": 0x1A, "reg_type": RegisterType.FUSE,
            "description": "SSE P1 ratio for SST PP0"
        },
        
        # Turbo ratio limit registers
        "socket0.computes.fuses.pcu.pcode_sst_pp_0_turbo_ratio_limit_ratios_cdyn_index0_ratio0": {
            "name": "turbo_ratio_0_0", "value": 0x20, "reg_type": RegisterType.FUSE,
            "description": "Turbo ratio limit for 1 active core"
        },
        
        # IO frequency ratios
        "socket0.ios.fuses.punit_iosf_sb.pcode_sst_pp_0_cfc_p0_ratio": {
            "name": "io_cfc_p0_ratio_pp0", "value": 0x10, "reg_type": RegisterType.FUSE,
            "description": "IO CFC P0 ratio for SST PP0"
        },
        "socket0.ios.fuses.punit_iosf_sb.pcode_cfc_pn_ratio": {
            "name": "io_cfc_pn_ratio", "value": 0x08, "reg_type": RegisterType.FUSE,
            "description": "IO CFC Pn ratio"
        },
        
        # VP2INTERSECT instruction fuses (complex pattern from configs)
        "socket0.computes.fuses.scf_gnr_maxi_coretile_c0_r1.core_core_fuse_misc_vp2intersect_dis": {
            "name": "vp2intersect_disable_c0_r1", "value": 0x1, "reg_type": RegisterType.FUSE,
            "description": "VP2INTERSECT instruction disable fuse for compute0 ring1"
        },
        
        # S2T register data patterns (from s2tregdata.json)
        "socket0.computes.cpu.cores.al_cr_alloc_pwrdn_ovrd": {
            "name": "alloc_pwrdn_ovrd", "value": 0x40000000, "reg_type": RegisterType.CONFIG,
            "description": "Optimistic Clock Power Down Overrides for the Alloc unit"
        },
        "socket0.computes.cpu.cores.al_cr_testmode": {
            "name": "alloc_testmode", "value": 0x155000000000, "bit_width": 64, "reg_type": RegisterType.CONFIG,
            "description": "Forces certain allocation state or control signal values for debug purposes"
        },
        "socket0.computes.cpu.cores.bpu1_cr_debug3": {
            "name": "bpu_debug3", "value": 0x4280000, "reg_type": RegisterType.CONFIG,
            "description": "BPU Debug 3 Control Register"
        },
        "socket0.computes.cpu.cores.ctap_cr_core_config_0": {
            "name": "core_config_0", "value": 0x86910800, "reg_type": RegisterType.CONFIG,
            "description": "Core config register 0 for Pcode/Ucode usage"
        },
        
        # DPM (Dynamic Power Management) counters
        "socket0.computes.cpu.cores.fscp_cr_core_c6_residency_counter": {
            "name": "c6_residency_counter", "value": 0x0, "reg_type": RegisterType.READ_ONLY,
            "description": "Core C6 residency counter"
        },
        "socket0.computes.uncore.punit.ptpcioregs.ptpcioregs.pc6_rcntr": {
            "name": "pc6_counter", "value": 0x0, "reg_type": RegisterType.READ_ONLY,
            "description": "Package C6 counter"
        },
        
        # Mesh/Cache registers (from s2tmeshdata.json)
        "socket0.computes.cpu.mesh.al_cr_arch_fuses": {
            "name": "mesh_arch_fuses", "value": 0x0, "bit_width": 64, "reg_type": RegisterType.READ_ONLY,
            "description": "Mesh architectural fuses cached from uncore"
        },
        "socket0.computes.cpu.mesh.core_cr_arch_fuses": {
            "name": "mesh_core_arch_fuses", "value": 0x0, "bit_width": 64, "reg_type": RegisterType.READ_ONLY,
            "description": "Core architectural fuses for mesh operations"
        },
        
        # TAP registers for debug/state dump (from decoder configs)
        "socket0.compute0.taps.scf_gnr_maxi_coretile_0_cpu_top_tca_tap": {
            "name": "coretile_0_tca_tap", "value": 0x0, "reg_type": RegisterType.CONFIG,
            "description": "Core tile 0 TCA TAP for state dump"
        },
        "socket0.compute0.taps.scf_gnr_maxi_coretile_0_cpu_tile_mtap": {
            "name": "coretile_0_mtap", "value": 0x0, "reg_type": RegisterType.CONFIG,
            "description": "Core tile 0 mesh TAP for state dump"
        },
    },
    
    "CWF": {
        # CWF Socket configuration registers
        "socket0.target_info.segment": {"name": "segment", "value": 0x435746, "reg_type": RegisterType.READ_ONLY},  # 'CWF'
        "socket0.target_info.chop": {"name": "chop", "value": 0x435746, "reg_type": RegisterType.READ_ONLY},
        "socket0.target_info.variant": {"name": "variant", "value": 0x455331, "reg_type": RegisterType.READ_ONLY},
        
        # Boot control registers (same as GNR)
        "socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg": {
            "name": "biosscratchpad6_cfg", "value": 0x0, "reset_value": 0x0,
            "description": "BIOS scratchpad for boot control"
        },
        
        # CWF-specific frequency ratios (similar structure to GNR)
        "socket0.computes.fuses.pcu.pcode_sst_pp_0_cfc_p0_ratio": {
            "name": "cfc_p0_ratio_pp0", "value": 0x16, "reg_type": RegisterType.FUSE,
            "description": "CFC P0 ratio for SST PP0 (CWF variant)"
        },
        "socket0.computes.fuses.pcu.pcode_sst_pp_0_cfc_p1_ratio": {
            "name": "cfc_p1_ratio_pp0", "value": 0x0E, "reg_type": RegisterType.FUSE,
            "description": "CFC P1 ratio for SST PP0 (CWF variant)"
        },
        "socket0.computes.fuses.pcu.pcode_cfc_pn_ratio": {
            "name": "cfc_pn_ratio", "value": 0x08, "reg_type": RegisterType.FUSE,
            "description": "CFC Pn ratio (CWF variant)"
        },
        
        # CWF IA ratios
        "socket0.computes.fuses.pcu.pcode_ia_p0_ratio": {
            "name": "ia_p0_ratio", "value": 0x1E, "reg_type": RegisterType.FUSE,
            "description": "IA P0 ratio (CWF variant)"
        },
        "socket0.computes.fuses.pcu.pcode_ia_pn_ratio": {
            "name": "ia_pn_ratio", "value": 0x08, "reg_type": RegisterType.FUSE,
            "description": "IA Pn ratio (CWF variant)"
        },
        
        # CWF IO ratios
        "socket0.ios.fuses.punit_iosf_sb.pcode_sst_pp_0_cfc_p0_ratio": {
            "name": "io_cfc_p0_ratio_pp0", "value": 0x0F, "reg_type": RegisterType.FUSE,
            "description": "IO CFC P0 ratio for SST PP0 (CWF variant)"
        },
        
        # CWF TAP registers (different core tile naming)
        "socket0.compute0.taps.scf_cwf_coretile_0_cpu_top_tca_tap": {
            "name": "cwf_coretile_0_tca_tap", "value": 0x0, "reg_type": RegisterType.CONFIG,
            "description": "CWF Core tile 0 TCA TAP for state dump"
        },
        
        # Core disable masks (CWF has no IOS according to configs)
        "socket0.pcudata.fused_ia_core_disable_0": {
            "name": "fused_ia_core_disable_0", "value": 0x0, "reg_type": RegisterType.READ_ONLY,
            "description": "CWF Fused IA core disable mask lower 32 bits"
        },
        
        # CWF burn-in voltage levels (from CWFBurnInFuses.json pattern)
        "socket0.computes.fuses.pcu.vcccore_burnin_high": {
            "name": "vcccore_burnin_high", "value": 0x5DC, "reg_type": RegisterType.FUSE,  # 1.5V in mV
            "description": "VCC Core burn-in high voltage level"
        },
        "socket0.computes.fuses.pcu.vcccore_burnin_low": {
            "name": "vcccore_burnin_low", "value": 0x41A, "reg_type": RegisterType.FUSE,  # 1.05V in mV
            "description": "VCC Core burn-in low voltage level"
        },
    },
    
    "DMR": {
        # DMR-specific registers (placeholder for future expansion)
        "socket0.target_info.segment": {"name": "segment", "value": 0x444D52, "reg_type": RegisterType.READ_ONLY},  # 'DMR'
        "socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg": {
            "name": "biosscratchpad6_cfg", "value": 0x0, "reset_value": 0x0,
            "description": "BIOS scratchpad for boot control"
        },
        # DMR registers will be added here when specifications are available
    }
}

# Global instances (will be replaced in TestMocks.py)
_mock_sv = None
_mock_ipc = None

def get_mock_sv(product: str = "GNR") -> MockSV:
    """Get or create mock SV instance"""
    global _mock_sv
    if _mock_sv is None:
        _mock_sv = MockSV(product)
        _mock_sv.initialize()
    return _mock_sv

def get_mock_ipc() -> MockIPC:
    """Get or create mock IPC instance"""
    global _mock_ipc
    if _mock_ipc is None:
        _mock_ipc = MockIPC()
    return _mock_ipc

def setup_hardware_mocks(product: str = "GNR"):
    """Set up hardware mocks in sys.modules"""
    import sys
    
    # Create mock instances
    mock_sv = get_mock_sv(product)
    mock_ipc = get_mock_ipc()
    
    # Replace in sys.modules
    sys.modules['namednodes'] = mock_sv
    sys.modules['ipccli'] = mock_ipc
    
    print(f"[HARDWARE MOCKS] Set up mocks for product: {product}")
    print(f"[HARDWARE MOCKS] SV initialized: {mock_sv._initialized}")
    print(f"[HARDWARE MOCKS] Register count: {len(mock_sv._register_map._registers)}")

if __name__ == "__main__":
    # Test the mock system
    print("Testing Hardware Mock System...")
    
    # Test SV interface
    sv = get_mock_sv("GNR")
    sv.initialize()
    
    print(f"Socket0 segment: {sv.socket0.target_info['segment']}")
    print(f"Computes: {sv.socket0.computes.name}")
    
    # Test register read/write
    sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg = 0xbf000000
    value = int(sv.socket0.io0.uncore.ubox.ncdecs.biosscratchpad6_cfg)
    print(f"Scratchpad value: 0x{value:x}")
    
    # Test IPC interface
    ipc = get_mock_ipc()
    print(f"IPC locked: {ipc.islocked()}")
    ipc.unlock()
    ipc.forcereconfig()
    ipc.go()
    
    print("Hardware mock system test completed.")