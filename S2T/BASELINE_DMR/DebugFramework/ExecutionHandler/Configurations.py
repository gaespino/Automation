"""
Framework Configuration Classes
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import time
import os
import sys

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

print(' -- Debug Framework Configurations -- rev 1.7')

sys.path.append(parent_dir)

from ExecutionHandler.Enums import ContentType, TestTarget, VoltageType, TestType, TestStatus

#########################################################
######		Debug Framework Configuration Code
#########################################################

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
	linux_pass_string: Optional[str] = None
	linux_fail_string: Optional[str] = None
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

# Configuration Classes
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
			'Post Process': 'post_process',
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
			'Disable 1 Core': 'dis1CPM',
			'Check Core': 'coreslice',
			'Voltage Type': 'volt_type',
			'Voltage IA': 'volt_IA',
			'Voltage CFC': 'volt_CFC',
			'Frequency IA': 'freq_ia',
			'Frequency CFC': 'freq_cfc',
			'External Mask': 'extMask',
			'Fuse File': 'fusefile',
			'Bios File': 'biosfile',
			'Slice Disable List': 'slicedislist',
			'Core Disable List': 'coredislist',
			'Temperature SP': 'tempsp',
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
	"Linux Pass String": "linux_pass_string",
	"Linux Fail String": "linux_fail_string",
	"Startup Linux": "linux_startup_cmd",
	"Linux Path": "linux_content_path",
	"Linux Content Wait Time": "linux_wait_time",
	"Linux Content Line 0": "Linux_content_line0",
	"Linux Content Line 1": "Linux_content_line1",
	"Linux Content Line 2": "Linux_content_line2",
	"Linux Content Line 3": "Linux_content_line3",
	"Linux Content Line 4": "Linux_content_line4",
	"Linux Content Line 5": "Linux_content_line5",
	"Linux Content Line 6": "Linux_content_line6",
	"Linux Content Line 7": "Linux_content_line7",
	"Linux Content Line 8": "Linux_content_line8",
	"Linux Content Line 9": "Linux_content_line9",
	}

	CUSTOM_MAPPING = {} # WIP

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
	dis1CPM: Optional[int] = None # Added for DMR
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
	#macro_files: Optional[str] = None
	macro_folder: Optional[str] = r'C:\SystemDebug\TTL'
	script_file: Optional[str] = None
	post_process: Optional[str] = None

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
	ttl_files_dict: Optional[Dict] = None  # Pre-copied TTL files
	ttl_path: Optional[str] = None         # Path to copied TTL files

	# Strategy and Test Info
	strategy_type: Optional[str] = None
	experiment_name: Optional[str] = None
	cancel_flag: bool= False # Cancellation Flag for external scripts
	execution_cancelled: bool = False
	execution_ended: bool = False

	# New Features
	biosfile: Optional[str] = None
	fusefile: Optional[str] = None
	coredislist: Optional[Dict] = None
	slicedislist: Optional[Dict] = None
	tempsp: Optional[float] = None

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
