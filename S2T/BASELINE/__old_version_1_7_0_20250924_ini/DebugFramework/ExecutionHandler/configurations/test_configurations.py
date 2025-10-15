from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import time
from ..enums.framework_enums import ContentType, TestTarget, VoltageType, TestType

@dataclass
class TestConfiguration:
    """Centralized test configuration"""
    # Basic test info
    name: str = 'Experiment'
    tnumber: int = 1
    ttype: str = TestType.LOOPS
    content: ContentType = ContentType.DRAGON
    visual: str = '-9999999'
    qdf: str = ''
    bucket: str = 'FRAMEWORK'
    target: TestTarget = TestTarget.MESH
    ttime: int = 30
    
    # Hardware settings
    mask: Optional[str] = None
    coreslice: Optional[int] = None
    pseudo: bool = False
    dis2CPM: Optional[int] = None
    corelic: Optional[int] = None
    
    # Voltage/Frequency settings
    volt_type: VoltageType = VoltageType.VBUMP
    volt_IA: Optional[float] = None
    volt_CFC: Optional[float] = None
    freq_ia: Optional[int] = None
    freq_cfc: Optional[int] = None
    
    # Platform settings
    host: str = "10.250.0.2"
    com_port: str = '8'
    u600w: bool = False
    
    # Test behavior
    reset: bool = True
    resetonpass: bool = False
    fastboot: bool = True
    
    # Files and paths
    macro_folder: Optional[str] = r'C:\SystemDebug\TTL'
    script_file: Optional[str] = None
    
    # Test conditions
    passstring: str = 'Test Complete'
    failstring: str = 'Test Failed'
    postcode_break: Optional[int] = None
    
    # Advanced settings
    extMask: Optional[Dict] = None
    
    # Runtime data (populated during execution)
    tfolder: Optional[str] = None
    log_file: Optional[str] = None
    data_bin: Optional[str] = None
    data_bin_desc: Optional[str] = None
    program: Optional[str] = None
    ser_log_file: Optional[str] = None
    ttl_files_dict: Optional[Dict] = None
    ttl_path: Optional[str] = None
    strategy_type: Optional[str] = None
    experiment_name: Optional[str] = None

@dataclass
class SystemToTesterConfig:
    """System to tester boot configuration"""
    AFTER_MRC_POST: int = 0xbf000000
    EFI_POST: int = 0xef0000ff
    LINUX_POST: int = 0x58000000
    BOOTSCRIPT_RETRY_TIMES: int = 3
    BOOTSCRIPT_RETRY_DELAY: int = 60
    MRC_POSTCODE_WT: int = 30
    EFI_POSTCODE_WT: int = 60
    MRC_POSTCODE_CHECK_COUNT: int = 5
    EFI_POSTCODE_CHECK_COUNT: int = 10
    BOOT_STOP_POSTCODE: int = 0x0
    BOOT_POSTCODE_WT: int = 30
    BOOT_POSTCODE_CHECK_COUNT: int = 10

@dataclass
class TestResult:
    """Encapsulates test execution results"""
    status: str
    name: str
    scratchpad: str = ""
    seed: str = ""
    timestamp: float = field(default_factory=time.time)
    iteration: int = 1
    log_path: Optional[str] = None
    config_path: Optional[str] = None
    pysv_log_path: Optional[str] = None