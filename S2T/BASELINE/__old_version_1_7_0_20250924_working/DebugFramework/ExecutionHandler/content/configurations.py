from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

@dataclass
class DragonConfiguration:
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

@dataclass
class LinuxConfiguration:
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

@dataclass
class ConfigurationMapping:
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