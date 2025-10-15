"""
Framework Configuration Classes
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import time

from .Enums import ContentType, TestTarget, VoltageType, TestType
from ..interfaces.IFramework import IConfigurationManager

@dataclass
class DragonConfiguration:
    """Dragon-specific configuration"""
    dragon_pre_cmd: Optional[str] = None
    dragon_post_cmd: Optional[str] = None
    dragon_startup_cmd: Optional[str] = None
    dragon_content_path: Optional[str] = None
    dragon_content_line: Optional[str] = None
    dragon_stop_on_fail: bool = False
    merlin_name: Optional[str] = None
    merlin_drive: Optional[str] = None
    merlin_npath: Optional[str] = None
    ulx_path: Optional[str] = None
    ulx_cpu: Optional[str] = None
    ulx_product: Optional[str] = None
    vvar0: Optional[str] = None
    vvar1: Optional[str] = None
    vvar2: Optional[str] = None
    vvar3: Optional[str] = None
    vvar_extra: Optional[str] = None
    apic_cdie: Optional[int] = None

    def validate(self) -> tuple[bool, List[str]]:
        """Validate dragon configuration"""
        errors = []
        
        if self.ulx_cpu and not self.ulx_path:
            errors.append("ULX path required when ULX CPU is specified")
            
        if self.apic_cdie is not None and not (0 <= self.apic_cdie <= 3):
            errors.append("APIC CDIE must be between 0 and 3")
            
        return len(errors) == 0, errors

@dataclass
class LinuxConfiguration:
    """Linux-specific configuration"""
    linux_pre_cmd: Optional[str] = None
    linux_post_cmd: Optional[str] = None
    linux_startup_cmd: Optional[str] = None
    linux_content_path: Optional[str] = None
    linux_wait_time: Optional[int] = None
    Linux_content_line0: Optional[int] = None
    Linux_content_line1: Optional[int] = None
    Linux_content_line2: Optional[int] = None
    Linux_content_line3: Optional[int] = None
    Linux_content_line4: Optional[int] = None
    Linux_content_line5: Optional[int] = None
    Linux_content_line6: Optional[int] = None
    Linux_content_line7: Optional[int] = None
    Linux_content_line8: Optional[int] = None
    Linux_content_line9: Optional[int] = None

    def validate(self) -> tuple[bool, List[str]]:
        """Validate linux configuration"""
        errors = []
        
        if self.linux_wait_time is not None and self.linux_wait_time < 0:
            errors.append("Linux wait time must be non-negative")
            
        return len(errors) == 0, errors

@dataclass
class TestConfiguration:
    """Centralized test configuration with validation"""
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

    # TTL Configuration
    ttl_files_dict: Optional[Dict] = None
    ttl_path: Optional[str] = None

    # Strategy and Test Info
    strategy_type: Optional[str] = None 
    experiment_name: Optional[str] = None

    def __post_init__(self):
        """Validate configuration after initialization"""
        is_valid, errors = self.validate()
        if not is_valid:
            from .exceptions import ConfigurationError
            raise ConfigurationError(f"Invalid configuration: {'; '.join(errors)}")

    def validate(self) -> tuple[bool, List[str]]:
        """Validate test configuration"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Test name cannot be empty")
            
        if self.ttime <= 0:
            errors.append("Test time must be positive")
            
        if self.volt_IA is not None and not (0.5 <= self.volt_IA <= 2.0):
            errors.append("IA voltage must be between 0.5V and 2.0V")
            
        if self.volt_CFC is not None and not (0.5 <= self.volt_CFC <= 2.0):
            errors.append("CFC voltage must be between 0.5V and 2.0V")
            
        if self.freq_ia is not None and not (100 <= self.freq_ia <= 6000):
            errors.append("IA frequency must be between 100MHz and 6000MHz")
            
        if self.freq_cfc is not None and not (100 <= self.freq_cfc <= 4000):
            errors.append("CFC frequency must be between 100MHz and 4000MHz")
            
        return len(errors) == 0, errors

@dataclass
class SystemToTesterConfig:
    """System to tester boot configuration with validation"""
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

    def validate(self) -> tuple[bool, List[str]]:
        """Validate S2T configuration"""
        errors = []
        
        if self.BOOTSCRIPT_RETRY_TIMES < 0:
            errors.append("Retry times must be non-negative")
            
        if self.BOOTSCRIPT_RETRY_DELAY < 0:
            errors.append("Retry delay must be non-negative")
            
        return len(errors) == 0, errors

@dataclass
class TestResult:
    """Encapsulates test execution results with enhanced metadata"""
    status: str
    name: str
    scratchpad: str = ""
    seed: str = ""
    timestamp: float = field(default_factory=time.time)
    iteration: int = 1
    log_path: Optional[str] = None
    config_path: Optional[str] = None
    pysv_log_path: Optional[str] = None
    execution_time: Optional[float] = None
    error_details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization"""
        return {
            'status': self.status,
            'name': self.name,
            'scratchpad': self.scratchpad,
            'seed': self.seed,
            'timestamp': self.timestamp,
            'iteration': self.iteration,
            'log_path': self.log_path,
            'config_path': self.config_path,
            'pysv_log_path': self.pysv_log_path,
            'execution_time': self.execution_time,
            'error_details': self.error_details
        }

class ConfigurationMapping:
    """Configuration mapping constants"""
    
    CONFIG_MAPPING = {
        'Test Name': 'name',
        'Test Mode': 'target',
        'Test Type': 'ttype',
        'Visual ID': 'visual',
        'Bucket': 'bucket',
        'COM Port': 'com_port',
        'IP Address': 'host',
        'TTL Folder': 'macro_folder',
        'Scripts File': 'script_file',
        'Pass String': 'passstring',
        'Fail String': 'failstring',
        'Content': 'content',
        'Test Number': 'tnumber',
        'Test Time': 'ttime',
        'Reset': 'reset',
        'Reset on PASS': 'resetonpass',
        'FastBoot': 'fastboot',
        'Core License': 'corelic',
        '600W Unit': 'u600w',
        'Pseudo Config': 'pseudo',
        'Configuration (Mask)': 'mask',
        'Boot Breakpoint': 'postcode_break',
        'Disable 2 Cores': 'dis2CPM',
        'Check Core': 'coreslice',
        'Voltage Type': 'volt_type',
        'Voltage IA': 'volt_IA',
        'Voltage CFC': 'volt_CFC',
        'Frequency IA': 'freq_ia',
        'Frequency CFC': 'freq_cfc',
        'External Mask': 'extMask',
    }
    
    DRAGON_MAPPING = {
        "Dragon Pre Command": "dragon_pre_cmd",
        "Dragon Post Command": "dragon_post_cmd",
        "Startup Dragon": "dragon_startup_cmd",
        "ULX Path": "ulx_path",
        "ULX CPU": "ulx_cpu",
        "Product Chop": "ulx_product",
        "VVAR0": "vvar0",
        "VVAR1": "vvar1",
        "VVAR2": "vvar2",
        "VVAR3": "vvar3",
        "VVAR_EXTRA": "vvar_extra",
        "Dragon Content Path": "dragon_content_path",
        "Dragon Content Line": "dragon_content_line",
        "Stop on Fail": "dragon_stop_on_fail",
        "Merlin Name": "merlin_name",
        "Merlin Drive": "merlin_drive",
        "Merlin Path": "merlin_npath"
    }

    LINUX_MAPPING = {
        "Linux Pre Command": "linux_pre_cmd",
        "Linux Post Command": "linux_post_cmd",
        "Startup Linux": "linux_startup_cmd",
        "Linux Path": "linux_content_path",
        "Linux Content Wait Time": "linux_wait_time",
        "Linux Content Line 0": "Linux_content_line0",
        "Linux Content Line 1": "Linux_content_line1"
    }

    CUSTOM_MAPPING = {}  # WIP

class FrameworkConfigurationManager(IConfigurationManager):
    """Implementation of configuration manager interface"""
    
    def load_config(self, source: str) -> Dict[str, Any]:
        """Load configuration from source"""
        # Implementation depends on your file handling system
        pass
    
    def save_config(self, config: Dict[str, Any], destination: str) -> bool:
        """Save configuration to destination"""
        # Implementation depends on your file handling system
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate configuration dictionary"""
        try:
            # Convert dict to TestConfiguration and validate
            test_config = TestConfiguration(**config)
            return test_config.validate()
        except Exception as e:
            return False, [str(e)]