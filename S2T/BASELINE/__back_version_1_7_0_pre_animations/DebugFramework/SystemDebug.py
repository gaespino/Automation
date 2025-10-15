import time
import os, sys
import ipccli
import namednodes
import pandas as pd
import time
import shutil
from tabulate import tabulate
from datetime import datetime
import pytz
import colorama
from colorama import Fore, Style, Back
from ipccli.stdiolog import log
from ipccli.stdiolog import nolog

# Handling/Interfacing/dataclass 

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
from enum import Enum
from abc import ABC, abstractmethod
import queue
import threading

# S2T scripts
import users.gaespino.dev.S2T.CoreManipulation as gcm
import users.gaespino.dev.S2T.dpmChecks as dpm
import users.gaespino.dev.S2T.SetTesterRegs as s2t
import users.gaespino.dev.DebugFramework.SerialConnection as ser
import users.gaespino.dev.DebugFramework.MaskEditor as gme
import users.gaespino.dev.DebugFramework.FileHandler as fh
import users.gaespino.dev.DebugFramework.UI.ControlPanel as fcp

# Utils 
import users.gaespino.dev.S2T.Tools.utils as s2tutils
import ExecutionHandler.utils.ThreadsHandler as th
import importlib

#from ExecutionHandler.utils.ThreadsHandler import execution_state, ExecutionCommand

importlib.reload(ser)
importlib.reload(gme)
importlib.reload(fh)
importlib.reload(fcp)
importlib.reload(s2tutils)
importlib.reload(th)

ExecutionCommand = th.ExecutionCommand
execution_state = th.execution_state

## DB Connection library
#try:
#	import users.gaespino.dev.DebugFramework.Storage_Handler.DBHandler as db
#	importlib.reload(db)
#	DATABASE_HANDLER_READY = True
#except Exception as e:
#	print(f' Unable to import Database Handler with Exception: {e}')
#	DATABASE_HANDLER_READY = False


# TEST MODE

USE_TEST_MODE_S2T = True

## Folders
script_dir = os.path.dirname(os.path.abspath(__file__))
base_folder = 'C:\\SystemDebug'
ttl_source = os.path.join(script_dir, 'TTL')
shmoos_source = os.path.join(script_dir, 'Shmoos')
ttl_dest = os.path.join(base_folder, 'TTL')
shmoos_dest = os.path.join(base_folder, 'Shmoos')
logs_dest = os.path.join(base_folder, 'Logs')

PYTHONSV_CONSOLE_LOG = r"C:\Temp\PythonSVLog.log"

ULX_CPU_DICT = {'GNR': 'GNR_B0',
		   'CWF': 'CWF -gsv'}

# Utils
def xformat(e):
	return s2tutils.formatException(e)

# Run Tera Term macros
def macros_path(ttl_path):
	macrospath = rf'{ttl_path}'
	macro_cmds = {
		'Disconnect': rf'{macrospath}\disconnect.ttl',
		'Connect': rf'{macrospath}\connect.ttl',
		'StartCapture':  rf'{macrospath}\Boot.ttl',
		'StartTest': rf'{macrospath}\Commands.ttl',
		'StopCapture':  rf'{macrospath}\stop_capture.ttl'
	}
	return macro_cmds
# Default Macros Path
macro_cmds = macros_path(ttl_dest)

#########################################################
######		Interfaces
#########################################################

from Interfaces.IFramework import IStatusReporter

#########################################################
######		Status Manager
#########################################################

class StatusEventType(Enum):
	# Experiment Level
	EXPERIMENT_START = "experiment_start"
	EXPERIMENT_END = "experiment_end"
	EXPERIMENT_FAILED = "experiment_failed"
	EXPERIMENT_CANCELLED = "experiment_cancelled"
	EXPERIMENT_PREPARED = "execution_prepared"
	EXPERIMENT_FINALIZED = "execution_finalized"
	EXPERIMENT_END_REQUESTED = "experiment_end_requested"
	EXPERIMENT_ENDED_BY_COMMAND = "experiment_ended_by_command"
	
	# Strategy Level
	STRATEGY_PROGRESS = "strategy_progress"
	STRATEGY_COMPLETE = "strategy_complete"
	STRATEGY_EXECUTION_COMPLETE = "strategy_execution_complete"
	
	# Iteration Level
	ITERATION_START = "iteration_start"
	ITERATION_PROGRESS = "iteration_progress"
	ITERATION_COMPLETE = "iteration_complete"
	ITERATION_FAILED = "iteration_failed"
	ITERATION_CANCELLED = "iteration_cancelled"
	
	# Command Level
	EXECUTION_HALTED = "execution_halted"
	EXECUTION_RESUMED = "execution_resumed"
	HALT_WAITING = "halt_waiting"

	# Step Mode
	STEP_MODE_ENABLED = "step_mode_enabled"
	STEP_MODE_DISABLED = "step_mode_disabled"
	STEP_ITERATION_COMPLETE = "step_iteration_complete"
	STEP_CONTINUE_ISSUED = "step_continue_issued"
	STEP_WAITING = "step_waiting"

@dataclass
class StatusContext:
	"""Context information for status updates"""
	experiment_name: Optional[str] = None
	strategy_type: Optional[str] = None
	test_name: Optional[str] = None
	current_iteration: int = 0
	total_iterations: int = 0
	additional_data: Dict[str, Any] = field(default_factory=dict)

class StatusUpdateManager:
	"""Lightweight status update manager that integrates with MainThreadHandler"""
	
	def __init__(self, status_reporter, logger=None):
		self.status_reporter = status_reporter  # Your MainThreadHandler instance
		self.logger = logger or print
		self.enabled = True
		self.context = StatusContext()
	
	def update_context(self, **kwargs):
		"""Update the current context"""
		for key, value in kwargs.items():
			if hasattr(self.context, key):
				setattr(self.context, key, value)
			else:
				self.context.additional_data[key] = value
	
	def send_update(self, event_type: StatusEventType, **additional_data):
		"""Send status update through your existing MainThreadHandler"""
		if not self.enabled:
			return
		
		try:
			# Build status data compatible with your MainThreadHandler
			status_data = {
				'type': event_type.value,
				'timestamp': datetime.now().isoformat(),
				'data': {
					# Core context
					'experiment_name': self.context.experiment_name,
					'strategy_type': self.context.strategy_type,
					'test_name': self.context.test_name,
					'iteration': self.context.current_iteration,
					'current_iteration': self.context.current_iteration,
					'total_iterations': self.context.total_iterations,
					
					# Additional context data
					**self.context.additional_data,
					
					# Event-specific data
					**additional_data
				}
			}
			
			# Apply event-specific transformations to match your handler expectations
			self._apply_event_transformations(status_data, event_type, additional_data)
			
			# Send through your existing status reporter
			if self.status_reporter:
				self.status_reporter.report_status(status_data)
				
			# Debug logging for progress updates
			if 'progress' in event_type.value:
				progress = additional_data.get('progress_percent', 0)
				if 'progress_weight' in additional_data:
					progress = additional_data['progress_weight'] * 100
				self.logger(f"DEBUG Framework Status: {event_type.value} - {progress:.1f}%")
				
		except Exception as e:
			self.logger(f"Status update error: {e}")
	
	def _apply_event_transformations(self, status_data: Dict, event_type: StatusEventType, additional_data: Dict):
		"""Apply transformations to match your MainThreadHandler expectations"""
		data = status_data['data']
		
		# Handle progress weight to progress percent conversion
		if 'progress_weight' in additional_data:
			data['progress_percent'] = additional_data['progress_weight'] * 100
		
		# Handle strategy progress specific formatting
		if event_type == StatusEventType.STRATEGY_PROGRESS:
			if 'progress_percent' not in additional_data and self.context.total_iterations > 0:
				data['progress_percent'] = (self.context.current_iteration / self.context.total_iterations) * 100
		
		# Handle iteration complete specific data
		if event_type == StatusEventType.ITERATION_COMPLETE:
			if 'scratchpad' in additional_data:
				data['scratchpad'] = additional_data['scratchpad']
			if 'seed' in additional_data:
				data['seed'] = additional_data['seed']
		
		# Handle strategy execution complete data
		if event_type == StatusEventType.STRATEGY_EXECUTION_COMPLETE:
			required_fields = [
				'total_executed', 'total_tests', 'planned_iterations', 
				'completed_normally', 'ended_by_command', 'final_stats',
				'success_rate', 'status_counts', 'failure_patterns'
			]
			for field in required_fields:
				if field in additional_data:
					data[field] = additional_data[field]
		
		# Handle step iteration complete data
		if event_type == StatusEventType.STEP_ITERATION_COMPLETE:
			if 'latest_result' in additional_data:
				data['latest_result'] = additional_data['latest_result']
			if 'current_stats' in additional_data:
				data['current_stats'] = additional_data['current_stats']
			if 'waiting_for_command' in additional_data:
				data['waiting_for_command'] = additional_data['waiting_for_command']
	
	def disable(self):
		"""Disable status updates"""
		self.enabled = False
	
	def enable(self):
		"""Enable status updates"""
		self.enabled = True
	
	def reset_context(self):
		"""Reset context for new execution"""
		self.context = StatusContext()

#########################################################
######		Exception Handling -- WIP
#########################################################

class BootFailureType(Enum):
	REGACC_FAILURE = "regacc_failure"
	GENERAL_FAILURE = "general_failure"
	TIMEOUT_FAILURE = "timeout_failure"
	CONFIGURATION_FAILURE = "config_failure"
	USER_CANCEL = "user_cancel"

class TestExecutionError(Exception):
	"""Custom exception for test execution errors"""
	def __init__(self, message: str, failure_type: BootFailureType = None, original_exception: Exception = None):
		super().__init__(message)
		self.failure_type = failure_type
		self.original_exception = original_exception

#########################################################
######		Debug Framework Configuration Code
#########################################################

# Enums for better type safety
class ContentType(Enum):
	DRAGON = "Dragon"
	LINUX = "Linux"
	PYSVCONSOLE = "PYSVConsole"
	BOOTBREAKS = "BootBreaks"
	CUSTOM = 'Custom' # Custom EFI TTL no need for Linux, that one is Custom by default

class ExecutionMode(Enum):
	CONTINUOUS = "continuous"
	STEP_BY_STEP = "step_by_step"

class TestTarget(Enum):
	MESH = "mesh"
	SLICE = "slice"

class VoltageType(Enum):
	VBUMP = "vbump"
	PPVC = "ppvc"
	FIXED = "fixed"

class TestStatus(Enum):
	SUCCESS = "Success"
	STARTED = "Started"
	CANCELLED = "CANCELLED"
	FAILED = "Failed"
	EXECUTION_FAIL = 'ExecutionFAIL'
	PYTHON_FAIL = 'PythonFail'
	PASS = "PASS"
	FAIL = "FAIL"

class TestType(Enum):
	SWEEP = "Sweep"
	SHMOO = "Shmoo"
	LOOPS = "Loops"

class ContentValues(Enum):
	PRODUCT = s2t.SELECTED_PRODUCT
	ULX_CPU = ULX_CPU_DICT[PRODUCT]

# Content Classes

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

#########################################################
######		Debug Framework Execution Code
#########################################################

# Core Test Execution
class TestExecutor:
	"""Handles individual test execution"""
	
	def __init__(self, config: TestConfiguration, s2t_config: SystemToTesterConfig, framework_instance ):
		self.config = config
		self.s2t_config = s2t_config
		self.cancel_flag = config.cancel_flag
		self.framework = framework_instance
		self.current_status = TestStatus.SUCCESS
		self._framework_callback = None # Set by Strategy
		self.status_manager = self.framework.status_manager

		# Initialize logging and paths
		self.execution_state = self.framework.execution_state
		self._setup_test_environment()
				
	def _check_cancellation(self):
		"""Enhanced cancellation check using framework command system"""
		if hasattr(self.config, 'execution_cancelled') and self.config.execution_cancelled:
			self.gdflog.log("Execution already cancelled - stopping immediately", 2)
			raise InterruptedError("Execution cancelled")

		command_result = self.framework._check_commands()
		
		if command_result == "CANCELLED":  # ✅ Handle CANCELLED status
			self.gdflog.log("CANCEL command received - stopping execution", 2)
			self.config.execution_cancelled = True
			raise InterruptedError("Execution cancelled")		
		elif command_result == "END_REQUESTED":
			self.gdflog.log("END command received - finishing current iteration", 2)
			# Don't raise exception, let iteration complete
			return

		elif command_result == "ERROR":
			raise InterruptedError("Command processing error")
		# PAUSED and CONTINUE are handled in framework._check_commands
				
	def _setup_test_environment(self):
		"""Setup test environment and logging"""
		# Test folder is already set up at strategy level in self.config.tfolder
		# Just ensure log files are properly configured
		#description = f'T{self.config.tnumber}_{self.config.name}'
		#self.config.tfolder = self.strategy_test_folder#fh.create_log_folder(logs_dest, description)
		self.config.log_file = os.path.join(self.config.tfolder, 'DebugFrameworkLogger.log')
		self.config.ser_log_file = ser.log_file_path
		
		# Initialize loggers
		self.gdflog = fh.FrameworkLogger(self.config.log_file, 'FrameworkLogger', console_output=True)
		self.pylog = fh.FrameworkLogger(PYTHONSV_CONSOLE_LOG, 'PythonSVLogger', pythonconsole=True)
		
		# Clear any previous cancellation flag -- removed passing the variable
		# Framework.clear_s2t_cancel_flag(self.gdflog.log)
		
		# Update system configuration
		self._update_system_config()
		
	def _update_system_config(self):
		"""Update global system configuration"""
		gcm.AFTER_MRC_POST = self.s2t_config.AFTER_MRC_POST
		gcm.EFI_POST = self.s2t_config.EFI_POST
		gcm.LINUX_POST = self.s2t_config.LINUX_POST
		gcm.BOOTSCRIPT_RETRY_TIMES = self.s2t_config.BOOTSCRIPT_RETRY_TIMES
		gcm.BOOTSCRIPT_RETRY_DELAY = self.s2t_config.BOOTSCRIPT_RETRY_DELAY
		gcm.MRC_POSTCODE_WT = self.s2t_config.MRC_POSTCODE_WT
		gcm.EFI_POSTCODE_WT = self.s2t_config.EFI_POSTCODE_WT
		gcm.MRC_POSTCODE_CHECK_COUNT = self.s2t_config.MRC_POSTCODE_CHECK_COUNT
		gcm.EFI_POSTCODE_CHECK_COUNT = self.s2t_config.EFI_POSTCODE_CHECK_COUNT
		gcm.BOOT_STOP_POSTCODE = self.s2t_config.BOOT_STOP_POSTCODE
		gcm.BOOT_POSTCODE_WT = self.s2t_config.BOOT_POSTCODE_WT
		gcm.BOOT_POSTCODE_CHECK_COUNT = self.s2t_config.BOOT_POSTCODE_CHECK_COUNT
		
		#if self.cancel_flag:
		#	gcm.cancel_flag = self.cancel_flag
	
	def execute_single_test(self) -> TestResult:
		"""Execute a single test iteration"""
		try:
			# Set up context for Status Updates
			self.status_manager.update_context(
					experiment_name=getattr(self.config, 'experiment_name', self.config.name),
					strategy_type=getattr(self.config, 'strategy_type', 'Unknown'),
					test_name=self.config.name,
					current_iteration=self.config.tnumber
				)
				
			# Marks execution as active
			self.execution_state.set_state('execution_active', True)
			
			# Check cancellation at start
			self._check_cancellation()
				
			# Send iteration start notification (0% of iteration)
			self.status_manager.send_update(
					StatusEventType.ITERATION_START,
					status='Starting Test Iteration',
					progress_weight=0.0
				)

			self._log_test_banner()
			
			# Kill Any previous Teraterm Process
			ser.kill_process(process_name='ttermpro.exe', logger=self.gdflog.log)

			# Prepare test environment (5% of iteration)
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Preparing Environment',
					progress_weight=0.05
				)
				
			# Prepare test environment
			boot_logging = self.config.content == ContentType.BOOTBREAKS
			wait_postcode = not self.config.u600w
			
			# Setup serial configuration
			exp_ttl_files_dict = self._get_ttl_files_from_config()
			test_name = self._generate_test_name()

			# Send boot start notification (10% of iteration)
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Starting Boot Process',
					progress_weight=0.10
				)
			
			serial = ser.teraterm(
				visual=self.config.visual,
				qdf=self.config.qdf,
				bucket=self.config.bucket,
				log=self.config.ser_log_file,
				cmds=exp_ttl_files_dict,
				tfolder=self.config.tfolder,
				test=test_name,
				ttime=self.config.ttime,
				tnum=self.config.tnumber,
				DebugLog=self.gdflog.log,
				chkcore=self.config.coreslice,
				content=self.config.content.value,
				host=self.config.host,
				PassString=self.config.passstring,
				FailString=self.config.failstring,
				execution_state = self.execution_state # Passing Framework object
			)
			
			# Start logging if needed
			if boot_logging:
				serial.boot_start()
			
			self._start_python_logging()

			# Execute test based on target (15-45% of iteration for boot process)
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='System Boot in Progress',
					progress_weight=0.15
				)		

			# Checks cancellation before boot
			self._check_cancellation() 

			# Execute test based on target
			boot_ready = self._execute_test_by_target()
			
			# Checks cancellation after boot
			self._check_cancellation() 
			
			# Send test execution notification (50% of iteration)
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Boot Process Complete',
					progress_weight=0.50,
					boot_ready=boot_ready
				)
						
			# Execute custom script if provided
			if self.config.script_file:
				self.status_manager.send_update(
						StatusEventType.ITERATION_PROGRESS,
						status='Executing Custom Script',
						progress_weight=0.55
					)
				self._execute_custom_script()
			
			self._stop_python_logging()

			# Handle test completion

			# Send test execution notification (50% of iteration)
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Running Test Content',
					progress_weight=0.60
				)

			if self.config.content == ContentType.PYSVCONSOLE:
				serial.PYSVconsole()
			elif self.config.content == ContentType.BOOTBREAKS:
				serial.boot_end()
			else:
				serial.run()

			# Handle test completion (75% of iteration)
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Test Content Complete - Processing Results',
					progress_weight=0.75
				)

			# Process results
			result = self._process_test_results(serial, test_name, boot_ready)

			# Process results (90% of iteration)
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Analyzing Results',
					progress_weight=0.90
				)
				
			if boot_ready:
				self.current_status = TestStatus.SUCCESS
			else:
				self.current_status = TestStatus.FAILED

			# Send iteration complete notification (100% of iteration)
			self.status_manager.send_update(
					StatusEventType.ITERATION_COMPLETE,
					status=result.status,
					scratchpad=result.scratchpad,
					seed=result.seed,
					progress_weight=1.0
				)
	
			return result

		except KeyboardInterrupt:
			self.current_status = TestStatus.CANCELLED
			self.execution_state.set_state('execution_active', False)
			
			self.status_manager.send_update(
					StatusEventType.ITERATION_CANCELLED,
					status='CANCELLED'
				)
			return TestResult(status="CANCELLED", name=self.config.name, iteration=self.config.tnumber)
			
		except InterruptedError:
			self.current_status = TestStatus.CANCELLED
			self.execution_state.set_state('execution_active', False)
			
			self.status_manager.send_update(
					StatusEventType.ITERATION_CANCELLED,
					status='CANCELLED'
				)
			return TestResult(status="CANCELLED", name=self.config.name, iteration=self.config.tnumber)
			
		except Exception as e:
			self.gdflog.log(f"Test execution failed: {xformat(e)}", 3)
			self.current_status = TestStatus.FAILED
			
			self.status_manager.send_update(
					StatusEventType.ITERATION_FAILED,
					status='FAILED',
					error=str(e)
				)
			return TestResult(status="FAILED", name=self.config.name, iteration=self.config.tnumber)
		finally:
			self.execution_state.set_state('execution_active', False)

	def _log_test_banner(self):
		"""Log test information banner"""
		self.gdflog.log(f' -- Test Start --- ')
		self.gdflog.log(f' -- Debug Framework {self.config.name} --- ')
		self.gdflog.log(f' -- Performing test iteration {self.config.tnumber} with the following parameters: ')
		
		# Log configuration details
		#self.gdflog.log(f'\t > Unit VisualID: {self.config.visual}')
		#self.gdflog.log(f'\t > Unit QDF: {self.config.qdf}')
		#self.gdflog.log(f'\t > Configuration: {self.config.mask or "System Mask"}')
		#self.gdflog.log(f'\t > Voltage set to: {self.config.volt_type.value}')
		#self.gdflog.log(f'\t > Core Freq: {self.config.freq_ia}')
		#self.gdflog.log(f'\t > Core Voltage: {self.config.volt_IA}')
		#self.gdflog.log(f'\t > Mesh Freq: {self.config.freq_cfc}')
		#self.gdflog.log(f'\t > Mesh Voltage: {self.config.volt_CFC}')
		#self.gdflog.log(f'\t > Running Content: {self.config.content.value}')

		EMPTY_FIELDS = [None, 'None', '']
		Configured_Mask = self.config.mask if self.config.extMask == None else "Custom"
		self.gdflog.log(f'\t > Unit VisualID: {self.config.visual}')
		self.gdflog.log(f'\t > PPV Program: {self.config.program}')
		self.gdflog.log(f'\t > PPV Bin: {self.config.data_bin}')
		self.gdflog.log(f'\t > PPV Bin Desc: {self.config.data_bin_desc}')
		self.gdflog.log(f'\t > Unit QDF: {self.config.qdf}')
		self.gdflog.log(f'\t > Configuration: {Configured_Mask if Configured_Mask not in EMPTY_FIELDS else "System Mask"} ')
		if self.config.corelic: self.gdflog.log(f'\t > Core License: {self.config.corelic} ')
		self.gdflog.log(f'\t > Voltage set to: {self.config.volt_type.value} ')
		self.gdflog.log(f'\t > HT Disabled (BigCore): {self.config.pseudo} ')
		self.gdflog.log(f'\t > Dis 2 Cores (Atomcore): {self.config.dis2CPM} ')
		self.gdflog.log(f'\t > Core Freq: {self.config.freq_ia} ')
		self.gdflog.log(f'\t > Core Voltage: {self.config.volt_IA} ')
		self.gdflog.log(f'\t > Mesh Freq: {self.config.freq_cfc} ')
		self.gdflog.log(f'\t > Mesh Voltage: {self.config.volt_CFC} ')
		self.gdflog.log(f'\t > Running Content: {self.config.content.value} ')
		self.gdflog.log(f'\t > Pass String: {self.config.passstring} ')
		self.gdflog.log(f'\t > Fail String: {self.config.failstring} ')

	def _get_ttl_files_from_config(self) -> Dict:
		"""Get TTL files from configuration (already copied at strategy level)"""
		if self.config.ttl_files_dict:
			self.gdflog.log("Using pre-copied TTL files from strategy setup", 1)
			if self.config.ttl_path:
				self.gdflog.log(f"TTL files location: {self.config.ttl_path}", 1)
			return self.config.ttl_files_dict
		else:
			# Fallback to default if no pre-copied files available
			self.gdflog.log("Using default TTL files (fallback)", 2)
			return macro_cmds
		
	def _generate_test_name(self) -> str:
		"""Generate test name based on configuration"""
		vbumps = self.config.volt_IA is not None or self.config.volt_CFC is not None
		vtstring = f'_vcfg_{self.config.volt_type.value}' if vbumps else ""
		iaF = f'_ia_f{self.config.freq_ia}' if self.config.freq_ia else ""
		cfcF = f'_cfc_f{self.config.freq_cfc}' if self.config.freq_cfc else ""
		iavolt = f'_ia_v{self.config.volt_IA}'.replace(".", "_") if self.config.volt_IA else ""
		cfcvolt = f'_cfc_v{self.config.volt_CFC}'.replace(".", "_") if self.config.volt_CFC else ""
		mask = self.config.mask or "System"
		
		return f'{self.config.name.strip()}_{mask}{iaF}{cfcF}{vtstring}{iavolt}{cfcvolt}'
	
	def _execute_test_by_target(self) -> bool:
		"""Execute test based on target (mesh/slice)"""
		boot_ready = False
		wait_postcode = not self.config.u600w
		self._check_cancellation()
		print('Boot Status: ', 'READY' if boot_ready else 'NOT_READY')
		try:
			# Send detailed boot progress updates

			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='System Boot in Progress - Starting S2T Flow',
					progress_weight=0.20
				)	
			
			self._execute_system2tester_flow()			

			# Boot process progressing
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='System Boot in Progress - S2T Flow Complete',
					progress_weight=0.35
				)	
		
			self._check_cancellation()
			boot_ready = True

			#print('Boot Status: ', 'READY' if boot_ready else 'NOT_READY')
			
		except KeyboardInterrupt:
			self.gdflog.log("Script interrupted by user. Exiting...",2)
			self.current_status = TestStatus.CANCELLED
			return False			
		except InterruptedError:
			self.gdflog.log("Script interrupted by user. Exiting...",2)
			self.current_status = TestStatus.CANCELLED
			return False
		except SyntaxError as se:
			print(f"Syntax error occurred: {se}")
			self.current_status = TestStatus.FAILED
			return False		
		except Exception as e:
			self.gdflog.log(f'Boot Failed with Exception {xformat(e)} --- Retrying.....', 4)

			# Send boot retry notification
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Boot Failed - Retrying',
					progress_weight=0.20
				)	
								
			if 'RSP 10' in str(e) or 'regaccfail' in str(e):
				self.gdflog.log('PowerCycling Unit -- RegAcc Fail during previous Boot', 4)
				self.framework.reboot_unit(wait_postcode=wait_postcode)
				#Framework.reconnect_ipc()
				gcm.svStatus(checkipc=True, checksvcores=False, refresh=False, reconnect=False)
			else:
				self.framework.reboot_unit(wait_postcode=wait_postcode)
			
			time.sleep(120)
			
			# Send boot retry notification
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Boot Failed - Retrying S2T Flow',
					progress_weight=0.20
				)	
			
			self._execute_system2tester_flow()

			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='System Boot in Progress - S2T Flow Complete',
					progress_weight=0.35
				)	
			
			boot_ready = True

		print('Boot Status: ', 'READY' if boot_ready else 'NOT_READY')

		# Boot completion
		self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Boot Process Complete',
					progress_weight=0.45
				)	

		return boot_ready

	def _execute_system2tester_flow(self):
		if USE_TEST_MODE_S2T:
			self.gdflog.log(' Framework in Test Mode ',2)
			self._check_cancellation()
			for i in range(30):
				self.gdflog.log(f' Framework in Test Mode: Test -- {i} ',2)
				self._check_cancellation()
				time.sleep(1)
		
		elif self.config.target == TestTarget.MESH:
				s2t.MeshQuickTest(
					core_freq=self.config.freq_ia,
					mesh_freq=self.config.freq_cfc,
					vbump_core=self.config.volt_IA,
					vbump_mesh=self.config.volt_CFC,
					Reset=self.config.reset,
					Mask=self.config.mask,
					pseudo=self.config.pseudo,
					dis_2CPM=self.config.dis2CPM,
					GUI=False,
					fastboot=self.config.fastboot,
					corelic=self.config.corelic,
					volttype=self.config.volt_type.value,
					debug=False,
					boot_postcode=(self.config.content == ContentType.BOOTBREAKS),
					extMask=self.config.extMask,
					execution_state = self.execution_state
				)
		elif self.config.target == TestTarget.SLICE:
				s2t.SliceQuickTest(
					Target_core=self.config.mask,
					core_freq=self.config.freq_ia,
					mesh_freq=self.config.freq_cfc,
					vbump_core=self.config.volt_IA,
					vbump_mesh=self.config.volt_CFC,
					Reset=self.config.reset,
					pseudo=False,
					dis_2CPM=self.config.dis2CPM,
					GUI=False,
					fastboot=self.config.fastboot,
					corelic=self.config.corelic,
					volttype=self.config.volt_type.value,
					debug=False,
					boot_postcode=(self.config.content == ContentType.BOOTBREAKS),
					execution_state = self.execution_state
				)

	def _execute_custom_script(self):
		"""Execute custom script if provided"""
		if self.config.content == ContentType.BOOTBREAKS:
			self.gdflog.log(f"Executing Custom script at reached boot Breakpoint: {self.config.script_file}", 1)
		elif self.config.content == ContentType.PYSVCONSOLE:
			self.gdflog.log(f"Executing Custom script before test: {self.config.script_file}", 1)
		
		fh.execute_file(file_path=self.config.script_file, logger=self.gdflog.log)
	
	def _start_python_logging(self):
		"""Start Python SV console logging"""
		if self.config.content in [ContentType.BOOTBREAKS, ContentType.PYSVCONSOLE]:
			log(PYTHONSV_CONSOLE_LOG, 'w')
		else:
			if self.pylog:
				self.pylog.start_capture('w')
	
	def _stop_python_logging(self):
		"""Stop Python SV console logging"""
		if self.config.content in [ContentType.BOOTBREAKS, ContentType.PYSVCONSOLE]:
			nolog()
		else:
			if self.pylog:
				self.pylog.stop_capture()
	
	def _process_test_results(self, serial, test_name: str, boot_ready: bool) -> TestResult:
		"""Process test results and save logs"""
		# Get test results
		result_parts = serial.testresult.split("::") if serial.testresult else ['NA', 'NA']
		run_status = result_parts[0] if boot_ready else TestStatus.EXECUTION_FAIL.value #"ExecutionFAIL"
		run_name = result_parts[-1]
		
		# Copy logs to test folder
		log_new_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}.log')
		pysvlog_new_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}_pysv.log')
		s2t_config_path = os.path.join(self.config.tfolder, f'{self.config.tnumber}_{test_name}.json')
		
		# Copy files if they exist
		if os.path.exists(self.config.ser_log_file):
			shutil.copy(self.config.ser_log_file, log_new_path)
		
		if os.path.exists(PYTHONSV_CONSOLE_LOG):
			shutil.copy(PYTHONSV_CONSOLE_LOG, pysvlog_new_path)
		
		if os.path.exists(r"C:\Temp\System2TesterRun.json"):
			shutil.copy(r"C:\Temp\System2TesterRun.json", s2t_config_path)
		
		# Extract additional information
		pass_strings = [s.strip() for s in self.config.passstring.split(",")]
		fail_strings = [s.strip() for s in self.config.failstring.split(",")]
		seed = fh.extract_fail_seed(log_file_path=log_new_path, PassString=pass_strings, FailString=fail_strings) if os.path.exists(log_new_path) else "NA"
		scratchpad = getattr(serial, 'scratchpad', '')
		
		# Log results
		self.gdflog.log(f'tdata_{self.config.tnumber}::{run_name}::{run_status}::{scratchpad}::{seed}')
		self.gdflog.log(print_custom_separator(f'Test iteration summary'))
		self.gdflog.log(f' -- Test Name: {run_name} --- ')
		self.gdflog.log(f' -- Test Result: {run_status} --- ')
		self.gdflog.log(f' -- Test End --- ')
		
		return TestResult(
			status=run_status,
			name=run_name,
			scratchpad=scratchpad,
			seed=seed,
			iteration=self.config.tnumber,
			log_path=log_new_path,
			config_path=s2t_config_path,
			pysv_log_path=pysvlog_new_path
		)

class TestResultProcessor:
	"""Utility class for processing and analyzing test results"""
	
	@staticmethod
	def create_shmoo_data(results: List[TestResult], test_type: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
		"""Create shmoo data and legends from test results (1D)"""
		shmoo_data = []
		legends = []
		fail_count = 0
		
		for result in results:
			if result.status == 'FAIL' or result.status == 'FAILED':
				fail_letter = chr(65 + fail_count)
				legends.append(f'{fail_letter} - {result.iteration}:{result.scratchpad}:{result.seed}')
				shmoo_data.append([fail_letter])
				fail_count += 1
			else:
				shmoo_data.append(["*"])
		
		shmoo_df = pd.DataFrame(shmoo_data, columns=[test_type])
		legends_df = pd.DataFrame(legends, columns=["Legends"])
		
		return shmoo_df, legends_df
	
	@staticmethod
	def create_2d_shmoo_data(results: List[TestResult], x_values: List[float], 
						   y_values: List[float]) -> Tuple[pd.DataFrame, pd.DataFrame]:
		"""Create 2D shmoo data for shmoo plots"""
		legends = []
		fail_count = 0
		
		# Create 2D array for shmoo data
		shmoo_matrix = []
		result_index = 0
		
		for y_val in y_values:
			row = []
			for x_val in x_values:
				if result_index < len(results):
					result = results[result_index]
					if result.status == 'FAIL'or result.status == 'FAILED':
						fail_letter = chr(65 + fail_count)
						legends.append(f'{fail_letter} - {result.iteration}:{result.scratchpad}:{result.seed}')
						row.append(fail_letter)
						fail_count += 1
					else:
						row.append("*")
					result_index += 1
				else:
					row.append("N/A")
			shmoo_matrix.append(row)
		
		shmoo_df = pd.DataFrame(shmoo_matrix, columns=x_values, index=y_values)
		legends_df = pd.DataFrame(legends, columns=["Legends"])
		
		return shmoo_df, legends_df
	
	@staticmethod
	def _calculate_status_counts(results):
		"""Calculate status counts for summary"""
		status_counts = {}
		for result in results:
			status = result.status.upper() if result.status else 'UNKNOWN'
			status_counts[status] = status_counts.get(status, 0) + 1
		return status_counts

	@staticmethod
	def _extract_failure_patterns(results):
		"""Extract failure patterns for summary"""
		failure_patterns = {}
		for result in results:
			if result.status == "FAIL" and result.scratchpad:
				pattern = result.scratchpad
				failure_patterns[pattern] = failure_patterns.get(pattern, 0) + 1
		return dict(sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True))
	
class TestContentBuilder:
	"""Utility class for processing and creating content files"""
	def __init__(self, data, dragon_config=None, linux_config=None, custom_config = None, logger = None, flow=None, core=None):
		self.logger = print if logger == None else logger
		self._data = data
		self._dragon_config = dragon_config
		self._linux_config = linux_config
		self._custom_config = custom_config
		self._flow = flow
		self._core = core

	def generate_ttl_configuration(self, content):
		
		self.logger(f">>> Generating TTL Config for: {content}",1)
		if content.lower() == 'dragon':
			config = self.generate_dragon_config()
		elif content.lower() == 'linux':
			config = self.generate_linux_config()
		elif content.lower() == 'custom':
			config = self.generate_custom_config()
		else:
			config = None			

		return config
	
	def generate_dragon_config(self) -> None:
		if self._dragon_config == None:
			self.logger(">>> Dragon Configuration not selected",3)
			return None
		
		self.logger(">>> Generating Dragon TTL Configuration",1)
		if self._flow and self._flow.upper() == "SLICE" and self._core:
			apic_cdie = dpm.get_compute_index(self._core)
			self.logger(f">>> Setting APIC CDIE to compute: {apic_cdie}",1)
			setattr(self._dragon_config, 'apic_cdie', apic_cdie)
		else:
			self.logger(f">>> APIC CDIE is not required when using flow: {self._flow.upper()}",1)
		
		self._generate_config(self._dragon_config)

		return self._dragon_config
			
	def generate_linux_config(self) -> None:
		if self._linux_config == None:
			self.logger(">>> Linux Configuration not selected",3)
			return None
		
		self.logger(">>> Generating Linux TTL Configuration",1)
		self._generate_config(self._linux_config)

		return self._linux_config

	def generate_custom_config(self) -> None:
		if self._custom_config == None:
			self.logger(">>> Linux Configuration not selected",3)
			return None
		
		self.logger(">>> Generating Custom TTL Configuration",1)
		self._generate_config(self._custom_config)

		return self._custom_config

	def _generate_config(self, config) -> List:

		for key, value in self._data.items():
			print(key,' : ',value)
			if hasattr(config, key):
				# Handle enum conversions
				
				setattr(config, key, value)
		
		return config

# Test Strategy Classes
class TestStrategy(ABC):
	"""Abstract base class for different test strategies"""
	
	@abstractmethod
	def execute(self, executor: TestExecutor) -> List[TestResult]:
		pass

class LoopTestStrategy(TestStrategy):
	"""Strategy for loop tests"""
	
	def __init__(self, loops: int):
		self.loops = loops
	
	def execute(self, executor: TestExecutor, halt_controller = None) -> List[TestResult]:
		results = []
		fail_count = 0
		
		# We do need Framework object here is a must
		if halt_controller == None:
			return ["FAILED", executor.config.name, executor.config.tnumber]
					
		# Initialize execution state
		# Prepare for execution
		halt_controller.execution_state.update_state(
				execution_active=True,
				total_iterations=self.loops,
				current_iteration=0,
				experiment_name=executor.config.name,
				waiting_for_step=False
			)

		# Store strategy type in config for status updates
		executor.config.strategy_type = 'Loops'		

		# Status Manager Context Update
		halt_controller.status_manager.update_context(
			strategy_type='Loops',
			total_iterations=self.loops
		)

		try:
			for i in range(self.loops):

				executor.config.tnumber = i + 1

				# Update current iteration in state
				halt_controller.execution_state.set_state('current_iteration', i + 1)
				halt_controller.status_manager.update_context(current_iteration=i + 1)

				# Check for commands before starting iteration
				command_result = halt_controller._check_commands()
				
				if command_result == "CANCELLED":
					executor.gdflog.log(f"CANCEL command received - stopping before iteration {i + 1}", 2)
					break
				elif command_result == "ERROR":
					executor.gdflog.log(f"Command processing error before iteration {i + 1}", 3)
					break

				# Send progress update
				halt_controller.status_manager.send_update(
						StatusEventType.STRATEGY_PROGRESS,
						progress_percent=round((i + 1) / self.loops * 100, 1),
						current_value=f"Loop {i + 1}/{self.loops}"
					)

				executor.gdflog.log(f'{print_separator_box(direction="down")}')	
				executor.gdflog.log(print_custom_separator(f'Running Loop iteration: {i + 1}/{self.loops}'))

				result = executor.execute_single_test()
				results.append(result)
				
				# Check for cancellation and break immediately
				if result.status == TestStatus.CANCELLED.value:
					executor.gdflog.log(f"LOOPS: Strategy execution cancelled at iteration {i + 1}", 2)
					break
				elif result.status == TestStatus.EXECUTION_FAIL.value:
					break
				elif result.status == TestStatus.PASS.value:
					executor.config.reset = executor.config.resetonpass
				else:
					executor.config.reset = True # Always reset if FAIL or any other condition
				
				executor.gdflog.log(f'{print_separator_box(direction="up")}')

				# Check for commands after iteration completion
				command_result = halt_controller._check_commands()
					
				# Debug logging
				#active_commands = halt_controller.execution_state.get_active_commands()
				#executor.gdflog.log(f"DEBUG: Active commands before check: {[cmd.name for cmd in active_commands]}", 1)
				
				#executor.gdflog.log(f"DEBUG: Command result: {command_result}", 1)

				if halt_controller.should_end_after_iteration():
					executor.gdflog.log(f"END command received - stopping after iteration {i + 1}", 2)
						
					# Send status update
					halt_controller.status_manager.send_update(
							StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
							completed_iterations=i + 1,
							reason='END command received after iteration completion',
							final_result=result.status
						)
						
					# Acknowledge the command
					#halt_controller.acknowledge_end_command(f"Strategy completed iteration {i + 1} and stopped")
					break

				if halt_controller.execution_state.is_step_mode_enabled():
					if i < self.loops - 1:  # Not the last iteration
						halt_controller.execution_state.set_state('waiting_for_step', True)
						command_result = halt_controller._check_commands()
						if command_result == "END_REQUESTED":
							break

				time.sleep(10)  # Brief pause between iterations

		# Update execution state
		except InterruptedError:
			executor.gdflog.log("Loop execution cancelled", 2)
			# Cancelled result if not already added
			if not results or results[-1].status != TestStatus.CANCELLED.value:
				results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=executor.config.tnumber))
		
		except Exception as e:
			executor.gdflog.log(f"Loop execution error: {e}", 3)
		finally:
			# Update execution state
			halt_controller.execution_state.set_state('execution_active', False)
			halt_controller.execution_state.set_state('waiting_for_step', False)
				
			# Send final summary
			final_stats = halt_controller._calculate_current_stats(results)
			halt_controller.status_manager.send_update(
						StatusEventType.STRATEGY_EXECUTION_COMPLETE,
						total_executed=len(results),
						total_tests=len(results),
						planned_iterations=self.loops,
						completed_normally=len(results) == self.loops and not halt_controller.execution_state.is_ended(),
						ended_by_command=halt_controller.execution_state.is_ended(),
						final_stats=final_stats,
						success_rate=final_stats.get('pass_rate', 0),
						status_counts=TestResultProcessor._calculate_status_counts(results),
						failure_patterns=TestResultProcessor._extract_failure_patterns(results)
					)
					
		return results

class SweepTestStrategy(TestStrategy):
	"""Strategy for sweep tests"""
	
	def __init__(self, ttype: str, domain: str, start: float, end: float, step: float):
		self.ttype = ttype
		self.domain = domain
		self.values = self._generate_range(start, end, step)
	
	def _generate_range(self, start: float, end: float, step: float) -> List[float]:
		"""Generate test values range"""
		if self.ttype == 'frequency':
			return list(range(int(start), int(end) + int(step), int(step)))
		elif self.ttype == 'voltage':
			values = []
			current = start
			while current <= end + step/2:  # Add small tolerance for float comparison
				values.append(round(current, 5))
				current += step
			return values
		else:
			raise ValueError(f"Invalid sweep type: {self.ttype}")
	
	def execute(self, executor: TestExecutor, halt_controller=None) -> List[TestResult]:
		results = []
		total_tests = len(self.values)
		
		# We do need Framework object here is a must
		if halt_controller == None:
			return ["FAILED", executor.config.name, executor.config.tnumber]
						
		# Initialize execution state
		halt_controller.execution_state.update_state(
			execution_active=True,
			total_iterations=total_tests,
			current_iteration=0,
			experiment_name=executor.config.name,
			waiting_for_step=False
		)

		# Store strategy type in config for status updates
		executor.config.strategy_type = 'Sweep'

		# Status Manager Context Update
		halt_controller.status_manager.update_context(
				strategy_type='Sweep',
				total_iterations=total_tests
			)

		try:
			for i, value in enumerate(self.values):
				executor.config.tnumber = i + 1
				self._update_config_value(executor.config, value)

				# Update current iteration in state
				
				halt_controller.execution_state.set_state('current_iteration', i + 1)
				halt_controller.status_manager.update_context(current_iteration=i + 1)

				# Check for commands before starting iteration
				
				command_result = halt_controller._check_commands()
				if command_result == "END_REQUESTED":
					executor.gdflog.log(f"Experiment ended by command before iteration {i + 1}", 2)
					break
				elif command_result == "ERROR":
					executor.gdflog.log(f"Command processing error before iteration {i + 1}", 3)
					break

				# Send progress update
				halt_controller.status_manager.send_update(
						StatusEventType.STRATEGY_PROGRESS,
						progress_percent=round((i + 1) / total_tests * 100, 1),
						current_value=f"{self.domain}={value}"
					)				

				executor.gdflog.log(f'{print_separator_box(direction="down")}')	
				executor.gdflog.log(f'Running Sweep iteration: {i + 1}/{total_tests}, {self.domain}={value}')
				
				result = executor.execute_single_test()
				results.append(result)
				
				# Check for cancellation and break immediately
				if result.status == TestStatus.CANCELLED.value:
					executor.gdflog.log(f"SWEEP: Strategy execution cancelled at iteration {i + 1}", 2)
					break
				elif result.status == TestStatus.EXECUTION_FAIL.value:
					break
				elif result.status == TestStatus.PASS.value:
					executor.config.reset = executor.config.resetonpass
				else:
					executor.config.reset = True # Always reset if FAIL or any other condition
				
				executor.gdflog.log(f'{print_separator_box(direction="up")}')

				# Check for commands after iteration completion
				
				command_result = halt_controller._check_commands()
					
				# Debug logging
				#active_commands = halt_controller.execution_state.get_active_commands()
				#executor.gdflog.log(f"DEBUG: Active commands before check: {[cmd.name for cmd in active_commands]}", 1)

				#executor.gdflog.log(f"DEBUG: Command result: {command_result}", 1)

				if halt_controller.should_end_after_iteration():
					executor.gdflog.log(f"END command received - stopping after iteration {i + 1}", 2)
					
					# Send status update
					if halt_controller.status_manager:
						halt_controller.status_manager.send_update(
							StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
							completed_iterations=i + 1,
							reason='END command received after iteration completion',
							final_result=result.status
						)
						
					# Acknowledge the command
					# halt_controller.acknowledge_end_command(f"Strategy completed iteration {i + 1} and stopped")
					break

				# Handle step-by-step mode
				if halt_controller.execution_state.is_step_mode_enabled():
					if i < total_tests - 1:  # Not the last iteration
						halt_controller.execution_state.set_state('waiting_for_step', True)
						command_result = halt_controller._check_commands()
						if command_result == "END_REQUESTED":
							break

				time.sleep(10)

		except InterruptedError:
			executor.gdflog.log("Sweep execution cancelled", 2)
			# Cancelled result if not already added
			if not results or results[-1].status != TestStatus.CANCELLED.value:
				results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=executor.config.tnumber))
		
		except Exception as e:
			executor.gdflog.log(f"Sweep execution error: {e}", 3)
		finally:
			# Update execution state

			halt_controller.execution_state.set_state('execution_active', False)
			halt_controller.execution_state.set_state('waiting_for_step', False)
				
			# Send final summary
			final_stats = halt_controller._calculate_current_stats(results)
			halt_controller.status_manager.send_update(
						StatusEventType.STRATEGY_EXECUTION_COMPLETE,
						total_executed=len(results),
						total_tests=len(results),
						planned_iterations=total_tests,
						completed_normally=len(results) == total_tests and not halt_controller.execution_state.is_ended(),
						ended_by_command=halt_controller.execution_state.is_ended(),
						final_stats=final_stats,
						success_rate=final_stats.get('pass_rate', 0),
						status_counts=TestResultProcessor._calculate_status_counts(results),
						failure_patterns=TestResultProcessor._extract_failure_patterns(results)
					)
		
		return results
	
	def _update_config_value(self, config: TestConfiguration, value: float):
		"""Update configuration with new test value"""
		if self.ttype == 'frequency':
			if self.domain == 'ia':
				config.freq_ia = int(value)
			elif self.domain == 'cfc':
				config.freq_cfc = int(value)
		elif self.ttype == 'voltage':
			if self.domain == 'ia':
				config.volt_IA = value
			elif self.domain == 'cfc':
				config.volt_CFC = value

class ShmooTestStrategy(TestStrategy):
	"""Strategy for shmoo tests"""
	
	def __init__(self, x_config: Dict, y_config: Dict):
		self.x_config = x_config
		self.y_config = y_config
		self.x_values = self._generate_range(x_config)
		self.y_values = self._generate_range(y_config)

	def get_axis_values(self) -> Tuple[List[float], List[float]]:
		"""Return the X and Y axis values for 2D shmoo plotting"""
		return self.x_values, self.y_values
	
	def _generate_range(self, config: Dict) -> List[float]:
		"""Generate range based on configuration"""
		ttype = config['Type']
		start = config['Start']
		end = config['End']
		step = config['Step']
		
		if ttype == 'frequency':
			return list(range(int(start), int(end) + int(step), int(step)))
		elif ttype == 'voltage':
			values = []
			current = start
			while current <= end + step/2:
				values.append(round(current, 5))
				current += step
			return values
	
	def execute(self, executor: TestExecutor, halt_controller=None) -> List[TestResult]:
		results = []
		iteration = 1
		total_tests = len(self.x_values) * len(self.y_values)
	
		# We do need Framework object here is a must
		if halt_controller == None:
			return ["FAILED", executor.config.name, executor.config.tnumber]
				
		# Initialize execution state
		halt_controller.execution_state.update_state(
				execution_active=True,
				total_iterations=total_tests,
				current_iteration=0,
				experiment_name=executor.config.name,
				waiting_for_step=False
			)
	
		halt_controller.status_manager.update_context(
			strategy_type='Shmoo',
			total_iterations=total_tests
			)			
	
		# Store strategy type in config for status updates
		executor.config.strategy_type = 'Shmoo'

		try:		
			for y_value in self.y_values:
				self._update_config_value(executor.config, self.y_config, y_value)

				for x_value in self.x_values:
					executor.config.tnumber = iteration
					self._update_config_value(executor.config, self.x_config, x_value)

					# Update current iteration in state
					halt_controller.execution_state.set_state('current_iteration', iteration)
					halt_controller.status_manager.update_context(current_iteration=iteration)

					# Check for commands before starting iteration
					command_result = halt_controller._check_commands()
					if command_result == "END_REQUESTED":
						executor.gdflog.log(f"Experiment ended by command before iteration {iteration}", 2)
						break
					elif command_result == "ERROR":
						executor.gdflog.log(f"Command processing error before iteration {iteration}", 3)
						break

					# Check for commands before starting iteration
					command_result = halt_controller._check_commands()
					if command_result == "END_REQUESTED":
						executor.gdflog.log(f"Experiment ended by command before iteration {iteration}", 2)
						break
					elif command_result == "ERROR":
						executor.gdflog.log(f"Command processing error before iteration {iteration}", 3)
						break

					# Send progress update

					halt_controller.status_manager.send_update(
						StatusEventType.STRATEGY_PROGRESS,
						progress_percent=round(iteration / total_tests * 100, 1),
						current_point=f"X={x_value}, Y={y_value}",
						x_axis=f"{self.x_config['Domain']}={x_value}",
						y_axis=f"{self.y_config['Domain']}={y_value}"
					)

					executor.gdflog.log(f'{print_separator_box(direction="down")}')	
					executor.gdflog.log(f'Running Shmoo iteration: {iteration}/{total_tests}')
					
					result = executor.execute_single_test()
					results.append(result)
						
					# Check for cancellation and break immediately
					if result.status == TestStatus.CANCELLED.value:
						executor.gdflog.log(f"SWEEP: Strategy execution cancelled at iteration {iteration}", 2)
						break
					elif result.status == TestStatus.EXECUTION_FAIL.value:
						break
					elif result.status == TestStatus.PASS.value:
						executor.config.reset = executor.config.resetonpass
					else:
						executor.config.reset = True # Always reset if FAIL or any other condition
					
					iteration += 1
					executor.gdflog.log(f'{print_separator_box(direction="up")}')

					# Check for commands after iteration completion
					
					command_result = halt_controller._check_commands()
						
					# Debug logging
					#active_commands = halt_controller.execution_state.get_active_commands()
					#executor.gdflog.log(f"DEBUG: Active commands before check: {[cmd.name for cmd in active_commands]}", 1)

					#executor.gdflog.log(f"DEBUG: Command result: {command_result}", 1)

					if halt_controller.should_end_after_iteration():
						executor.gdflog.log(f"END command received - stopping after iteration {iteration}", 2)
							
						# Send status update
						halt_controller.status_manager.send_update(
							StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
							completed_iterations=iteration,
							reason='END command received after iteration completion',
							final_result=result.status
						)
							
						# Acknowledge the command
						# halt_controller.acknowledge_end_command(f"Strategy completed iteration {iteration} and stopped")
						break


					# Handle step-by-step mode
					if halt_controller.execution_state.is_step_mode_enabled():
						if iteration < total_tests:  # Not the last iteration
							halt_controller.execution_state.set_state('waiting_for_step', True)
							command_result = halt_controller._check_commands()
							if command_result == "END_REQUESTED":
								break

					time.sleep(10)
		except InterruptedError:
			executor.gdflog.log("Shmoo execution cancelled", 2)
			# Cancelled result if not already added
			if not results or results[-1].status != TestStatus.CANCELLED.value:
				results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=executor.config.tnumber))
		
		except Exception as e:
			executor.gdflog.log(f"Shmoo execution error: {e}", 3)
		finally:
			# Update execution state
			
			halt_controller.execution_state.set_state('execution_active', False)
			halt_controller.execution_state.set_state('waiting_for_step', False)
				
			# Send final summary
			final_stats = halt_controller._calculate_current_stats(results)
			halt_controller.status_manager.send_update(
					StatusEventType.STRATEGY_EXECUTION_COMPLETE,
					total_executed=len(results),
					total_tests=len(results),
					planned_iterations=total_tests,
					completed_normally=len(results) == total_tests and not halt_controller.execution_state.is_ended(),
					ended_by_command=halt_controller.execution_state.is_ended(),
					final_stats=final_stats,
					success_rate=final_stats.get('pass_rate', 0),
					status_counts=TestResultProcessor._calculate_status_counts(results),
					failure_patterns=TestResultProcessor._extract_failure_patterns(results),
					shmoo_dimensions=f"{len(self.x_values)}x{len(self.y_values)}",
					x_axis_config=self.x_config,
					y_axis_config=self.y_config
				)
	
		return results
	
	def _update_config_value(self, config: TestConfiguration, axis_config: Dict, value: float):
		"""Update configuration with new test value"""
		ttype = axis_config['Type']
		domain = axis_config['Domain']
		
		if ttype == 'frequency':
			if domain == 'ia':
				config.freq_ia = int(value)
			elif domain == 'cfc':
				config.freq_cfc = int(value)
		elif ttype == 'voltage':
			if domain == 'ia':
				config.volt_IA = value
			elif domain == 'cfc':
				config.volt_CFC = value

#########################################################
######		Debug Framework Main Code
#########################################################

# Main Framework Class
class Framework:
	"""Main framework class with static methods for interface compatibility"""
	
	def __init__(self, upload_to_database: bool = True, status_reporter: Optional[IStatusReporter] = None):
		self.upload_to_database = upload_to_database
		self.config = TestConfiguration()
		self.s2t_config = SystemToTesterConfig()
		self.dragon_content = DragonConfiguration()
		self.linux_content = LinuxConfiguration()
		self.content_config = None
		self.unit_data = None
		self._current_strategy = None
		self._current_executor = None

		# CRITICAL: Use queue-based status reporting instead of direct callback
		self.status_manager = StatusUpdateManager(
			status_reporter=status_reporter,  # Your MainThreadHandler instance
			logger=self.FrameworkPrint
		)
		
		# Disable Send Updates if Status reporter is not included
		if status_reporter == None: 
			self.status_manager.disable()
		#self._status_queue = queue.Queue()
		#self._status_reporter = status_reporter
		#self._status_enabled = True

		# Status callback system
		#self.status_callback = status_callback
		self._current_test_stats = {}

		# More targeted control - only disable during critical command processing
		#self._status_updates_enabled = True
		#self._processing_critical_command = False  # New flag for critical operations

		# Execution Control
		self.cancel_flag = False # Cancellation flow checks on external scripts (S2T)
		self.execution_state = execution_state

		# Halt/Continue control
		self._halt_flag = threading.Event()
		self._continue_flag = threading.Event()
		self._command_lock = threading.Lock()
		self._is_halted = False

		# Progress tracking
		self.current_experiment_name = None
		self.current_experiment_total = 0
		self.current_experiment_completed = 0

		# Unified END command control (works in both modes)
		self._end_experiment_flag = threading.Event()
		self._end_command_lock = threading.Lock()
		
		# Step-by-step execution control
		self._step_mode_enabled = False
		self._step_continue_flag = threading.Event()
		self._iteration_complete_flag = threading.Event()
		self._step_command_lock = threading.Lock()

		# Add thread tracking
		self._execution_thread = None
		self._execution_thread_lock = threading.Lock()
	
		# Current execution state for external monitoring
		self._current_execution_state = {
			'is_running': False,
			'current_iteration': 0,
			'total_iterations': 0,
			'iteration_results': [],
			'current_stats': {},
			'waiting_for_command': False,
			'experiment_name': None,
			'end_requested': False
		}

	# ==================== COMMAND INTERFACE METHODS ====================
	
	def end_experiment(self):
		"""End current experiment after current iteration completes"""
		if not self.execution_state.get_state('execution_active'):
			self.FrameworkPrint("No experiment currently running", 2)
			return False
		
		def end_callback(response):
			self.FrameworkPrint(f"End experiment acknowledged: {response}", 1)
		
		success = self.execution_state.end_experiment(callback=end_callback)
		if success:
			self.FrameworkPrint("END EXPERIMENT command issued", 1)
			# Send status update through the status reporter
			self.status_manager.send_update(
				StatusEventType.EXPERIMENT_END_REQUESTED,
				message='End command issued - will complete current iteration and stop'
			)
		return success
	
	def halt_execution(self):
		"""Halt test execution after current iteration completes"""
		if not self.execution_state.get_state('execution_active'):
			self.FrameworkPrint("No execution to halt", 2)
			return False
		
		def halt_callback(response):
			self.FrameworkPrint(f"Halt acknowledged: {response}", 1)
		
		success = self.execution_state.pause(callback=halt_callback)
		if success:
			self.FrameworkPrint("HALT command issued", 1)
			self.status_manager.send_update(StatusEventType.EXECUTION_HALTED)
		return success
	
	def continue_execution(self):
		"""Continue halted test execution"""
		if not self.execution_state.is_paused():
			self.FrameworkPrint("No halted execution to continue", 2)
			return False
		
		def continue_callback(response):
			self.FrameworkPrint(f"Continue acknowledged: {response}", 1)
		
		success = self.execution_state.resume(callback=continue_callback)
		if success:
			self.FrameworkPrint("CONTINUE command issued", 1)
			self.status_manager.send_update(StatusEventType.EXECUTION_RESUMED)
		return success
	
	def cancel_execution(self):
		"""Cancel test execution"""
		def cancel_callback(response):
			self.FrameworkPrint(f"Cancel acknowledged: {response}", 1)
		
		success = self.execution_state.cancel(callback=cancel_callback)
		if success:
			self.FrameworkPrint("CANCEL command issued", 1)
			# Set old cancel flag for backward compatibility
			#if self.cancel_flag:
			#	self.cancel_flag.set()
		return success
	
	def enable_step_by_step_mode(self):
		"""Enable step-by-step execution mode"""
		success = self.execution_state.enable_step_mode()
		if success:
			self.FrameworkPrint("Step-by-step mode enabled", 1)
			self.status_manager.send_update(
				StatusEventType.STEP_MODE_ENABLED,
				message='Step-by-step execution mode enabled'
			)
		return success
	
	def disable_step_by_step_mode(self):
		"""Disable step-by-step execution mode"""
		success = self.execution_state.disable_step_mode()
		if success:
			self.FrameworkPrint("Step-by-step mode disabled", 1)
			self.status_manager.send_update(
				StatusEventType.STEP_MODE_DISABLED,
				message='Step-by-step execution mode disabled - switching to continuous mode'
			)
		return success
	
	def step_continue(self):
		"""Continue to next iteration in step-by-step mode"""
		if not self.execution_state.is_step_mode_enabled():
			self.FrameworkPrint("Step-by-step mode is not enabled", 2)
			return False
		
		if not self.execution_state.get_state('waiting_for_step'):
			self.FrameworkPrint("No iteration waiting for continue command", 2)
			return False
		
		def step_callback(response):
			self.FrameworkPrint(f"Step continue acknowledged: {response}", 1)
		
		success = self.execution_state.step_continue(callback=step_callback)
		if success:
			self.FrameworkPrint("STEP CONTINUE command issued", 1)
			self.status_manager.send_update(StatusEventType.STEP_CONTINUE_ISSUED)		
		return success
	
	# ==================== COMMAND CHECKING METHODS ====================
	
	def _check_commands(self):
		"""Check and process commands (called from background thread)"""
		try:
			# Check for cancellation FIRST (highest priority)
			if self.execution_state.is_cancelled():
				#self.execution_state.acknowledge_command(ExecutionCommand.CANCEL, "Cancellation processed")
				self.execution_state.start_processing_command(ExecutionCommand.CANCEL)
				if self.execution_state.has_command(ExecutionCommand.EMERGENCY_STOP):
					self.execution_state.start_processing_command(ExecutionCommand.EMERGENCY_STOP)
					#self.execution_state.acknowledge_command(ExecutionCommand.EMERGENCY_STOP, "Emergency stop processed")
				
				# Set persistent cancellation state in config
				if hasattr(self, 'config'):
					self.config.execution_cancelled = True
				
				return "CANCELLED"
				#raise InterruptedError("Execution cancelled")
			
			# Check for end experiment SECOND (allow current iteration to complete)
			if self.execution_state.is_ended():
				#self.execution_state.acknowledge_command(ExecutionCommand.END_EXPERIMENT, "End experiment processed")
				self.execution_state.start_processing_command(ExecutionCommand.END_EXPERIMENT)
				# Set persistent cancellation state in config
				if hasattr(self, 'config'):
					self.config.execution_ended = True

				return "END_REQUESTED"

			# Check for pause
			if self.execution_state.is_paused():
				self._handle_pause_command()
				return "PAUSED"
			
			# Check for step continue in step mode
			if self.execution_state.is_step_mode_enabled():
				return self._handle_step_mode()
			
			return "CONTINUE"
			
		except Exception as e:
			self.FrameworkPrint(f"Error checking commands: {e}", 3)
			return "ERROR"
	
	def _handle_pause_command(self):
		"""Handle pause command"""
		self.execution_state.acknowledge_command(ExecutionCommand.PAUSE, "Execution paused")
		self.FrameworkPrint("Execution paused - waiting for resume command", 1)
		
		# Wait for resume command
		while self.execution_state.is_paused():
			if self.execution_state.is_cancelled():
				raise InterruptedError("Cancelled while paused")
			time.sleep(0.1)  # Small delay to prevent busy waiting
		
		# Resume acknowledged
		self.execution_state.acknowledge_command(ExecutionCommand.RESUME, "Execution resumed")
		self.FrameworkPrint("Execution resumed", 1)
	
	def _handle_step_mode(self):
		"""Handle step-by-step mode"""
		if self.execution_state.get_state('waiting_for_step'):
			self.FrameworkPrint("Waiting for step continue command...", 1)
			
			while not self.execution_state.should_step_continue():
				if self.execution_state.is_cancelled():
					raise InterruptedError("Cancelled while waiting for step")
				if self.execution_state.is_ended():
					return "END_REQUESTED"
				time.sleep(0.1)
			
			# Step continue received
			self.execution_state.acknowledge_command(ExecutionCommand.STEP_CONTINUE, "Step continue processed")
			self.execution_state.set_state('waiting_for_step', False)
			self.FrameworkPrint("Step continue received - proceeding", 1)
		
		return "CONTINUE"

	# Not Used ?
	def _wait_for_step_command(self, current_iteration: int, total_iterations: int, 
							  latest_result: TestResult, logger=None) -> bool:
		"""Wait for step command after iteration completion"""
		if not self._step_mode_enabled:
			return True  # Continue normally if step mode disabled
		
		# Check if end was requested before waiting
		if self._check_end_experiment_request():
			return False
		
		log_func = logger.log if logger else self.FrameworkPrint
		
		# Update execution state
		with self._step_command_lock:
			self._current_execution_state['waiting_for_command'] = True
			self._current_execution_state['current_iteration'] = current_iteration
			
			# Add latest result to history
			if latest_result:
				self._current_execution_state['iteration_results'].append(latest_result)
		
		# Calculate and send current statistics
		current_stats = self._calculate_current_stats(self._current_execution_state['iteration_results'])
		
		# Send iteration complete notification with stats
		self.status_manager.update_context(
			current_iteration=current_iteration,
			total_iterations=total_iterations
		)
		
		self.status_manager.send_update(
			StatusEventType.STEP_WAITING,  # This will be handled by your StatusHandler
			next_iteration=current_iteration + 1,
			available_commands=['step_continue', 'end_experiment', 'cancel_execution'],
			latest_result={
				'iteration': latest_result.iteration,
				'status': latest_result.status,
				'scratchpad': latest_result.scratchpad,
				'seed': latest_result.seed
			} if latest_result else None,
			current_stats=current_stats,
			waiting_for_command=True
		)
		
		log_func(f"=== STEP-BY-STEP: Iteration {current_iteration}/{total_iterations} COMPLETED ===", 1)
		log_func(f"Latest Result: {latest_result.status} - {latest_result.scratchpad}" if latest_result else "No result", 1)
		log_func(f"Current Stats: {current_stats['pass_count']} PASS, {current_stats['fail_count']} FAIL, {current_stats['pass_rate']}% pass rate", 1)
		log_func("Waiting for external command:", 1)
		log_func("  - framework.step_continue()     # Continue to next iteration", 1)
		log_func("  - framework.end_experiment()    # End experiment after current iteration", 1)
		log_func("  - framework.cancel_execution()  # Cancel immediately", 1)
		log_func("  - framework.get_execution_state() # Get current state", 1)
		
		# Wait for command
		while True:
			# Check for end experiment command (highest priority)
			if self._check_end_experiment_request():
				log_func("=== EXPERIMENT ENDED BY END COMMAND ===", 2)
				
				self.status_manager.send_update(
					StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
					completed_iterations=current_iteration,
					reason='END command received during step wait',
					final_result=latest_result.status if latest_result else 'Unknown'
				)
				return False
			
			# Check for continue command
			if self._step_continue_flag.wait(timeout=1.0):
				self._step_continue_flag.clear()  # Reset for next iteration
				log_func("=== CONTINUING TO NEXT ITERATION ===", 1)
				
				self.status_manager.send_update(
					StatusEventType.STEP_CONTINUE_ISSUED,
					next_iteration=current_iteration + 1,
					message='Step continue command processed'
				)
				
				return True
			
			# Check for cancellation (existing functionality)
			if self.cancel_flag and self.cancel_flag.is_set():
				log_func("Execution cancelled by user", 2)
				
				self.status_manager.send_update(
					StatusEventType.ITERATION_CANCELLED,
					status='CANCELLED',
					reason='User cancellation during step wait'
				)
				return False

	# Not Used?
	def _wait_for_continue_or_cancel(self, current_iteration: int, total_iterations: int = None, logger=None):
		"""Wait for continue or cancel command when halted"""
		if not self._halt_flag.is_set():
			return True  # Not halted, continue normally
		
		# Use provided logger or fallback to FrameworkPrint
		log_func = logger.log if logger else self.FrameworkPrint
		
		total_str = f"/{total_iterations}" if total_iterations else ""
		log_func(f"=== EXECUTION HALTED after iteration {current_iteration}{total_str} ===", 1)
		log_func("Waiting for command: use continue_execution() or cancel_execution()", 1)
		log_func("Commands available:", 1)
		log_func("  - framework.continue_execution()  # Resume execution", 1)
		log_func("  - framework.cancel_execution()    # Cancel execution", 1)

		self.status_manager.update_context(
			current_iteration=current_iteration,
			total_iterations=total_iterations or 0
			)
		
		self.status_manager.send_update(
			StatusEventType.EXECUTION_HALTED,
			message=f'Execution halted after iteration {current_iteration}{total_str}',
			waiting_for_command=True,
			available_commands=['continue_execution', 'cancel_execution']
			)
		
		# Wait for either continue or cancel
		while True:
			# Check if cancel was requested
			if self.cancel_flag and self.cancel_flag.is_set():
				log_func("Execution cancelled by user", 2)

				self.status_manager.send_update(
					StatusEventType.ITERATION_CANCELLED,
					status='CANCELLED',
					reason='User cancellation during halt wait'
				)
				return False
			
			# Wait for continue flag with timeout to check cancel periodically
			if self._continue_flag.wait(timeout=1.0):
				log_func("=== EXECUTION RESUMED ===", 1)
				self.status_manager.send_update(
					StatusEventType.EXECUTION_RESUMED,
					message=f'Execution resumed from iteration {current_iteration}{total_str}'
				)
				return True
			
			# Continue checking in the loop

	def acknowledge_cancel_command(self, reason="Execution fully cancelled"):
		"""Acknowledge CANCEL command after full processing"""
		if self.execution_state.has_command(ExecutionCommand.CANCEL):
			self.execution_state.acknowledge_command(ExecutionCommand.CANCEL, reason)
			self.FrameworkPrint(f"CANCEL command acknowledged: {reason}", 1)
			return True
		return False

	def should_end_after_iteration(self) -> bool:
		"""Simple check if END command was issued - only call this at end of iterations"""
		return self.execution_state.has_command(ExecutionCommand.END_EXPERIMENT)

	def acknowledge_end_command(self, reason="Experiment ended after iteration completion"):
		"""Acknowledge END command after processing"""
		if self.execution_state.has_command(ExecutionCommand.END_EXPERIMENT):
			self.execution_state.acknowledge_command(ExecutionCommand.END_EXPERIMENT, reason)
			self.FrameworkPrint(f"END command acknowledged: {reason}", 1)
			return True
		return False

	# ==================== STATE MANAGEMENT ====================

	def _prepare_for_new_execution(self):
		"""Prepare framework for new execution"""
		try:
			self.FrameworkPrint("Preparing framework for new execution", 1)
			
			# Add a small delay to let any background command processing complete
			time.sleep(0.2)
			
			# Reset execution state with force cleanup
			success = self.execution_state.prepare_for_execution()
			if not success:
				self.FrameworkPrint("Failed to prepare execution state", 3)
				return False
			
			# Double-check that commands are really cleared
			active_commands = self.execution_state.get_active_commands()
			if active_commands:
				self.FrameworkPrint(f"WARNING: Commands still active after prepare: {[cmd.name for cmd in active_commands]}", 2)
				# Force clear them
				self.execution_state.clear_all_commands()
				
			# Reset framework-specific state
			self._current_execution_state = {
				'is_running': False,
				'current_iteration': 0,
				'total_iterations': 0,
				'iteration_results': [],
				'current_stats': {},
				'waiting_for_command': False,
				'experiment_name': None,
				'end_requested': False
			}
			
			# Send status update if reporter is available
			self.status_manager.send_update(
				StatusEventType.EXPERIMENT_PREPARED,
				message='Framework prepared for new execution'
			)
			
			self.FrameworkPrint("Framework prepared for new execution", 1)

			# Reset cancellation state
			if hasattr(self.config, 'execution_cancelled'):
				self.config.execution_cancelled = False

			# Reset end command state
			if hasattr(self.config, 'execution_ended'):
				self.config.execution_ended = False
			
			return True
			
		except Exception as e:
			self.FrameworkPrint(f"Error preparing for execution: {e}", 3)
			return False
	
	def _finalize_execution(self, reason="completed"):
		"""Finalize execution and cleanup"""
		try:
			self.FrameworkPrint(f"Finalizing execution: {reason}", 1)
			
			# Finalize execution state
			self.execution_state.finalize_execution(reason)
			
			# Send final status
			self.status_manager.send_update(
				StatusEventType.EXPERIMENT_FINALIZED,
				reason=reason
			)
			
			self.FrameworkPrint(f"Execution finalized: {reason}", 1)
			
		except Exception as e:
			self.FrameworkPrint(f"Error finalizing execution: {e}", 3)

	def _calculate_current_stats(self, results: List[TestResult]) -> Dict[str, Any]:
		"""Calculate current statistics from test results"""
		if not results:
			return {
				'total_completed': 0,
				'pass_count': 0,
				'fail_count': 0,
				'cancelled_count': 0,
				'execution_fail_count': 0,
				'other_count': 0,
				'pass_rate': 0.0,
				'fail_rate': 0.0,
				'valid_tests': 0,
				'latest_status': 'None',
				'latest_iteration': 0
			}
		
		# Count different result types
		status_counts = {}
		for result in results:
			status = result.status.upper() if result.status else 'UNKNOWN'
			status_counts[status] = status_counts.get(status, 0) + 1
		
		# Calculate specific counts
		pass_count = (status_counts.get('PASS', 0) + 
					status_counts.get('SUCCESS', 0) + 
					status_counts.get('*', 0))
		
		fail_count = (status_counts.get('FAIL', 0) + 
					status_counts.get('FAILED', 0) + 
					status_counts.get('ERROR', 0))
		
		cancelled_count = status_counts.get('CANCELLED', 0)
		execution_fail_count = status_counts.get('EXECUTIONFAIL', 0)
		
		total_completed = len(results)
		
		# Calculate valid tests (excluding cancelled and execution failures)
		valid_tests = total_completed - cancelled_count - execution_fail_count
		
		# Calculate other/unknown status count
		other_count = total_completed - pass_count - fail_count - cancelled_count - execution_fail_count
		
		# Calculate rates
		if valid_tests > 0:
			pass_rate = (pass_count / valid_tests) * 100
			fail_rate = (fail_count / valid_tests) * 100
		else:
			pass_rate = 0.0
			fail_rate = 0.0
		
		# Get latest result info
		latest_result = results[-1] if results else None
		latest_status = latest_result.status if latest_result else 'None'
		latest_iteration = latest_result.iteration if latest_result else 0
		
		return {
			'total_completed': total_completed,
			'pass_count': pass_count,
			'fail_count': fail_count,
			'cancelled_count': cancelled_count,
			'execution_fail_count': execution_fail_count,
			'other_count': other_count,
			'pass_rate': round(pass_rate, 1),
			'fail_rate': round(fail_rate, 1),
			'valid_tests': valid_tests,
			'latest_status': latest_status,
			'latest_iteration': latest_iteration,
			'status_breakdown': status_counts,
			'success_rate': round(pass_rate, 1)  # Alias for pass_rate for compatibility
		}

	def _get_strategy_total_iterations(self, strategy: TestStrategy) -> int:
		"""Get total number of iterations for a strategy"""
		if isinstance(strategy, LoopTestStrategy):
			return strategy.loops
		elif isinstance(strategy, SweepTestStrategy):
			return len(strategy.values)
		elif isinstance(strategy, ShmooTestStrategy):
			return len(strategy.x_values) * len(strategy.y_values)
		return 0

	def _reset_execution_state(self):
		"""Reset all execution state and commands for new execution"""
		try:
			self.FrameworkPrint("Resetting execution state for new run", 1)
			
			# Clear all active commands
			self.execution_state.clear_all_commands()
			
			# Reset execution state
			self.execution_state.update_state(
				execution_active=False,
				current_experiment=None,
				current_iteration=0,
				total_iterations=0,
				waiting_for_step=False,
				framework_ready=True
			)
			
			# Reset step mode if it was enabled (optional - you might want to keep this)
			# self.execution_state.set_state('step_mode_enabled', False)
			
			# Clear old cancel flag for backward compatibility
			#if self.cancel_flag:
			#	self.cancel_flag.clear()
			
			# Reset any framework-specific state
			self._current_execution_state = {
				'is_running': False,
				'current_iteration': 0,
				'total_iterations': 0,
				'iteration_results': [],
				'current_stats': {},
				'waiting_for_command': False,
				'experiment_name': None,
				'end_requested': False
			}
			
			self.FrameworkPrint("Execution state reset complete", 1)
			
		except Exception as e:
			self.FrameworkPrint(f"Error resetting execution state: {e}", 3)

	# ==================== EXECUTION METHODS ======================

	def _create_executor(self) -> TestExecutor:
		"""Create test executor with current configuration"""
		return TestExecutor(
							config=self.config, 
							s2t_config=self.s2t_config, 
							framework_instance=self)

	def _execute_strategy_and_process_results(self, strategy: TestStrategy, test_type: str) -> List[str]:
		"""Execute strategy and process results"""
		

		# Store current thread reference
		with self._execution_thread_lock:
			self._execution_thread = threading.current_thread()
		
		try:
			self._current_strategy = strategy
			
			# Prepare for new execution
			if not self._prepare_for_new_execution():
				self.FrameworkPrint("Failed to prepare for execution", 3)
				return ["FAILED"]


			# Get total iterations for this experiment
			total_iterations = self._get_strategy_total_iterations(strategy)
			
			# NEW: Update status manager context once
			self.status_manager.update_context(
				experiment_name=self.current_experiment_name or self.config.name,
				strategy_type=test_type,
				test_name=self.config.name,
				total_iterations=total_iterations
			)
			
			# Update Status Manager -- Experiment Start
			self.status_manager.send_update(StatusEventType.EXPERIMENT_START)
			
			# Setup TTL files and test environment once per strategy
			Framework.FrameworkPrint(f"Setting up {test_type} test environment...", 1)
			self._setup_strategy_environment()

			# Create executor
			executor = self._create_executor()
			self._current_executor = executor

			# Define logging
			executor.gdflog.log(f"Starting {test_type} test execution...", 1)
					
			Framework.FrameworkPrint(f"Starting {test_type} test execution...", 1)
			results = strategy.execute(executor, halt_controller=self)
			
			BAD_RESULTS = ["CANCELLED", "ExecutionFAIL"]

			# Generate summary and send to UI
			if results and results[-1].status not in BAD_RESULTS:
				summary_data = self._generate_summary_data(results, test_type)

				# Update Status Manager -- Strategy Complete
				self.status_manager.send_update(event_type=StatusEventType.STRATEGY_COMPLETE, **summary_data)

				self._generate_summary(results, test_type, self.config.tfolder, executor)
			else:
				# Update Status Manager -- Fail Summary
				self.status_manager.send_update(
					event_type=StatusEventType.EXPERIMENT_FAILED,
					reason=results[-1].status if results else 'Unknown',
					completed_iterations=len(results)
				)
			
			return [result.status for result in results]
				
		except Exception as e:
			self.FrameworkPrint(f"Error in strategy execution: {e}", 3)
			return ["ERROR"]  # Return error status if exception occurs
			
		finally:
			# Clear thread reference when done (this always executes)
			with self._execution_thread_lock:
				if self._execution_thread == threading.current_thread():
					self._execution_thread = None
					
			# Clean up executor reference
			self._current_executor = None
			self._current_strategy = None

	def get_execution_status(self) -> Dict[str, Any]:
		"""Get current execution status"""
		status = {
			"is_running": self._current_executor is not None,
			"is_halted": self._is_halted,
			"current_test": None,
			"strategy_type": None
		}
		
		if self._current_executor:
			status["current_test"] = {
				"name": self._current_executor.config.name,
				"iteration": self._current_executor.config.tnumber,
				"status": self._current_executor.current_status.value if hasattr(self._current_executor.current_status, 'value') else str(self._current_executor.current_status)
			}
		
		if self._current_strategy:
			status["strategy_type"] = type(self._current_strategy).__name__
			
		return status

	def get_execution_state(self) -> Dict[str, Any]:
		"""Get current execution state for external monitoring"""
		with self._step_command_lock:
			# Calculate current statistics
			results = self._current_execution_state['iteration_results']
			stats = self._calculate_current_stats(results)
			
			return {
				'execution_mode': self.config.execution_mode.value if hasattr(self.config, 'execution_mode') else 'continuous',
				'step_mode_enabled': self._step_mode_enabled,
				'is_running': self._current_execution_state['is_running'],
				'waiting_for_command': self._current_execution_state['waiting_for_command'],
				'end_requested': self._current_execution_state['end_requested'],
				'current_iteration': self._current_execution_state['current_iteration'],
				'total_iterations': self._current_execution_state['total_iterations'],
				'experiment_name': self._current_execution_state['experiment_name'],
				'current_stats': stats,
				'latest_results': results[-5:] if results else [],  # Last 5 results
				'available_commands': self._get_available_commands()
			}

	def _get_available_commands(self) -> List[str]:
		"""Get list of available commands based on current state"""
		commands = []
		
		if self._current_execution_state['is_running']:
			commands.extend(['end_experiment', 'cancel_execution', 'get_execution_state'])
			
			if self._step_mode_enabled:
				if self._current_execution_state['waiting_for_command'] and not self._current_execution_state['end_requested']:
					commands.append('step_continue')
				
				if not self._current_execution_state['is_running']:
					commands.append('disable_step_by_step_mode')
			else:
				commands.extend(['halt_execution'])
				if self._is_halted:
					commands.append('continue_execution')
		else:
			commands.extend(['enable_step_by_step_mode'])
			
		return commands

	def print_execution_status(self):
		"""Print current execution status"""
		"""Print current execution status"""
		status = self.get_execution_status()
		
		# Use executor logger if available, otherwise FrameworkPrint
		log_func = (self._current_executor.gdflog.log 
				   if self._current_executor and hasattr(self._current_executor, 'gdflog') 
				   else lambda msg, level: self.FrameworkPrint(msg, level))
		
		log_func("=== EXECUTION STATUS ===", 1)
		log_func(f"Running: {status['is_running']}", 1)
		log_func(f"Mode: {status.get('execution_mode', 'continuous')}", 1)
		log_func(f"End Requested: {status.get('end_requested', False)}", 1)
		
		if self._step_mode_enabled:
			log_func(f"Step Mode: Enabled", 1)
			log_func(f"Waiting for Command: {status['waiting_for_command']}", 1)
		else:
			log_func(f"Halted: {status.get('is_halted', False)}", 1)
		
		if status.get('current_test'):
			test = status['current_test']
			log_func(f"Current Test: {test['name']} (iteration {test['iteration']})", 1)
			log_func(f"Test Status: {test['status']}", 1)
		
		if status.get('strategy_type'):
			log_func(f"Strategy: {status['strategy_type']}", 1)
		
		log_func(f"Available Commands: {', '.join(status.get('available_commands', []))}", 1)
		log_func("========================", 1)
	
	def _check_end_experiment_request(self) -> bool:
		"""Check if experiment end was requested"""
		return self._end_experiment_flag.is_set()

	# ==================== CONFIGURATION MANAGEMENT ==================

	def update_unit_data(self):
		"""Update unit data from system"""
		try:
			self.config.qdf = dpm.qdf_str()
			self.unit_data = dpm.request_unit_info()
			
			if self.unit_data:
				system_visual = self.unit_data.get('VISUAL_ID', [None])[0]
				if system_visual and self.config.visual != system_visual:
					self.FrameworkPrint(f"Updating Visual ID: {self.config.visual} -> {system_visual}", 1)
					self.config.visual = system_visual
				
				self.config.data_bin = self.unit_data.get('DATA_BIN', [None])[0]
				self.config.data_bin_desc = self.unit_data.get('data_bin_desc', [None])[0]
				self.config.program = self.unit_data.get('PROGRAM', [None])[0]
		except Exception as e:
			self.FrameworkPrint(f"Failed to update unit data: {xformat(e)}", 2)

	def _get_current_flow_type(self):
		"""Get current flow type based on framework configuration"""
		if hasattr(self.config, 'content') and self.config.content == ContentType.LINUX:
			return "LINUX"
		elif hasattr(self.config, 'content') and self.config.content == ContentType.CUSTOM:
			return "CUSTOM"
		elif hasattr(self.config, 'target') and self.config.content == ContentType.DRAGON:
			if self.config.target == TestTarget.MESH:
				return "MESH"
			elif self.config.target == TestTarget.SLICE:
				return "SLICE"
		
		# Default fallback
		return None
	
	def get_config_updates(self, data, config_mapping):

		config_updates = {}
		for recipe_key, config_key in config_mapping.items():
			if recipe_key in data and data[recipe_key] is not None:
				value = data[recipe_key]
				
				# Handle special conversions
				if recipe_key == 'Disable 2 Cores' and value:
					config_updates['dis2CPM'] = int(value, 16)
				elif recipe_key == 'Core License' and value:
					config_updates['corelic'] = int(value.split(":")[0])
				elif recipe_key == 'Test Mode' and value:
					config_updates['target'] = value.lower()
				else:
					config_updates[config_key] = value

		return config_updates

	def get_content_updates(self, data, config_mapping):

		config_updates = {}
		for recipe_key, config_key in config_mapping.items():
			if recipe_key in data and data[recipe_key] is not None:
				value = data[recipe_key]
				if recipe_key == 'Dragon Content Line' and value:
					config_updates['dragon_content_line'] = " ".join(s.strip() for s in value.split(","))
				else:
					config_updates[config_key] = value

		return config_updates
	
	def update_configuration(self, **kwargs):
		"""Update test configuration"""
		for key, value in kwargs.items():
			if hasattr(self.config, key):
				# Handle enum conversions
				print(key,' : ',value)
				if key == 'content' and isinstance(value, str):
					value = ContentType(value)
				elif key == 'target' and isinstance(value, str):
					value = TestTarget(value)
				elif key == 'volt_type' and isinstance(value, str):
					value = VoltageType(value)
				
				setattr(self.config, key, value)

	def update_ttl_configuration(self, config_updates, flow):
		
		content = TestContentBuilder(
								data=config_updates, 
							   	dragon_config=self.dragon_content, 
							   	linux_config=self.linux_content, 
							   	custom_config=None, 
							   	logger = Framework.FrameworkPrint, 
								flow=flow, 
								core=self.config.mask)

		return content.generate_ttl_configuration(self.config.content.value)

	def _copy_ttl_files_to_config(self) -> Dict:
		"""Copy TTL files once for the entire test strategy"""
		if not self.config.macro_folder:
			Framework.FrameworkPrint("Using default TTL files (no macro folder specified)", 1)
			self.config.ttl_files_dict = macro_cmds
			self.config.ttl_path = ttl_dest # Default Value
			return   # Default TTL files
		
		Framework.FrameworkPrint(f"Copying TTL files from: {self.config.macro_folder}", 1)
		
		replace = 'Y'
		self.config.ttl_path = fh.create_path(folder=self.config.tfolder, file='TTL')
		fh.create_folder_if_not_exists(self.config.ttl_path)
		fh.copy_files(self.config.macro_folder, self.config.ttl_path, uinput=replace)
		
		self.config.ttl_files_dict = macros_path(self.config.ttl_path)
		Framework.FrameworkPrint(f"TTL files copied to: {self.config.ttl_path}", 1)

	# ==================== END SUMMARY METHODS ==================

	def _generate_summary_data(self, results: List[TestResult], test_type: str) -> Dict[str, Any]:
		"""Generate summary data for UI"""
		total_tests = len(results)
		if total_tests == 0:
			return {}
		
		# Count different result types
		status_counts = {}
		for result in results:
			status_counts[result.status] = status_counts.get(result.status, 0) + 1
		
		# Calculate success rate
		valid_tests = total_tests - status_counts.get('CANCELLED', 0) - status_counts.get('ExecutionFAIL', 0)
		passed_tests = status_counts.get('PASS', 0) + status_counts.get('*', 0)
		success_rate = (passed_tests / valid_tests * 100) if valid_tests > 0 else 0
		
		# Get failure patterns
		failure_patterns = {}
		for result in results:
			if result.status == "FAIL" and result.scratchpad:
				pattern = result.scratchpad
				failure_patterns[pattern] = failure_patterns.get(pattern, 0) + 1
		
		return {
			'strategy_type': test_type,
			'test_name': self.config.name,
			'total_tests': total_tests,
			'status_counts': status_counts,
			'success_rate': round(success_rate, 1),
			'valid_tests': valid_tests,
			'failure_patterns': dict(sorted(failure_patterns.items(), key=lambda x: x[1], reverse=True)),
			'first_fail_iteration': next((r.iteration for r in results if r.status == "FAIL"), None),
			'execution_time': results[-1].timestamp - results[0].timestamp if results else 0
		}

	def _generate_summary(self, results: List[TestResult], test_type: str, tfolder: str, executor: TestExecutor):
		"""Generate test summary and upload data"""
		# Use TestResultProcessor to create appropriate shmoo data
		
		logger = executor.gdflog

		# Log test series completion
		logger.log(print_custom_separator(f'{test_type} Test Series Completed'), 1)
		
		# Log individual test results first
		logger.log('Individual Test Results:', 1)
		logger.log('-' * 80, 1)
		logger.log(f"{'Iteration':<10} {'Status':<15} {'Name':<30} {'Scratchpad':<15} {'Seed':<10}", 1)
		logger.log('-' * 80, 1)

		for result in results:
			
			logger.log(
				f"{result.iteration:<10} {result.status:<15} {result.name[:29]:<30} "
				f"{result.scratchpad[:14]:<15} {result.seed[:9]:<10}", 1
			)
			
			
		# Check if we should skip upload based on test results
		should_upload = self._should_upload_data(results, logger)

		logger.log('-' * 80, 1)

		if test_type == "Shmoo" and isinstance(self._current_strategy, ShmooTestStrategy):
			# For 2D shmoo, get the axis values from the strategy
			x_values, y_values = self._current_strategy.get_axis_values()
			shmoo_df, legends_df = TestResultProcessor.create_2d_shmoo_data(
				results, x_values, y_values
			)
				
			logger.log(f'\n2D Shmoo Plot Configuration:', 1)
			logger.log(f'X-axis ({self._current_strategy.x_config["Type"]} - {self._current_strategy.x_config["Domain"]}): {x_values}', 1)
			logger.log(f'Y-axis ({self._current_strategy.y_config["Type"]} - {self._current_strategy.y_config["Domain"]}): {y_values}', 1)
			logger.log(f'Matrix Dimensions: {shmoo_df.shape[0]} rows x {shmoo_df.shape[1]} columns', 1)
			
		else:
			# For 1D tests (loops, sweeps), use the regular method
			shmoo_df, legends_df = TestResultProcessor.create_shmoo_data(results, test_type)
		
		# Log the shmoo matrix
		logger.log(f'\n{test_type} Results Matrix:', 1)
		logger.log('=' * 50, 1)
		
		# For better formatting in logs, convert to string with proper spacing
		shmoo_str = shmoo_df.to_string(max_cols=None, max_rows=None)
		for line in shmoo_str.split('\n'):
			if line.strip():  # Only log non-empty lines
				logger.log(line, 1)
		
		# Log legends
		logger.log('\nFailure Legends:', 1)
		logger.log('=' * 30, 1)
		if not legends_df.empty:
			for idx, row in legends_df.iterrows():
				logger.log(f"{row['Legends']}", 1)
		else:
			logger.log('No failures recorded - All tests passed!', 1)		

		self._log_test_statistics(results, logger)

		# Upload data Definition
		if should_upload:
			logger.log('\nData Upload Process:', 1)
			logger.log('=' * 30, 1)
			WW = str(dpm.getWW())
			product = s2t.SELECTED_PRODUCT
			
			datahandler = fh.TestUpload(
				folder=tfolder,
				vid=self.config.visual,
				name=self.config.name,
				bucket=self.config.bucket,
				WW=WW,
				product=product,
				logger= logger.log,
				from_Framework=True,
				upload_to_disk=True,
				upload_to_danta=self.upload_to_database
			)
			
			datahandler.generate_summary()
				
			# Print results
			#logger.log(f'{test_type} Test Results:')
			#logger.log(shmoo_df)
			#logger.log('\nLegends:')
			#logger.log(legends_df)

			datahandler.upload_data()
			logger.log('Database upload completed successfully', 1)

		else:
			self._log_upload_skipped_reason(results, logger)
		
		# Final completion message
		logger.log(print_custom_separator(f'{test_type} Summary Generation Completed'), 1)
			
	def _should_upload_data(self, results: List[TestResult], logger) -> bool:
		"""Determine if data should be uploaded based on test results"""
		if not results:
			logger.log('No results to evaluate for upload decision', 2)
			return False
		
		# Check for critical failure conditions
		critical_statuses = {'CANCELLED', 'ExecutionFAIL', 'FAILED'}
		
		# Count critical failures
		critical_failures = sum(1 for result in results if result.status in critical_statuses)
		total_tests = len(results)
		
		# If more than 50% of tests have critical failures, skip upload
		critical_failure_rate = critical_failures / total_tests if total_tests > 0 else 0
		
		# Check if the last test (most recent) had a critical failure
		last_test_critical = results[-1].status in critical_statuses
		
		# Check if ALL tests failed critically
		all_critical = all(result.status in critical_statuses for result in results)
		
		# Decision logic
		if all_critical:
			logger.log('Upload skipped: All tests had critical failures', 2)
			return False
		elif last_test_critical and critical_failure_rate > 0.5:
			logger.log(f'Upload skipped: Last test failed critically and {critical_failure_rate:.1%} of tests had critical failures', 2)
			return False
		elif critical_failure_rate >= 0.8:  # 80% or more critical failures
			logger.log(f'Upload skipped: {critical_failure_rate:.1%} of tests had critical failures', 2)
			return False
		else:
			# Check if we have any successful tests
			successful_tests = sum(1 for result in results if result.status not in {'FAILED', 'CANCELLED', 'ExecutionFAIL'})
			if successful_tests == 0:
				logger.log('Upload skipped: No successful tests found', 2)
				return False
			
			logger.log(f'Upload approved: {successful_tests}/{total_tests} tests successful, {critical_failure_rate:.1%} critical failure rate', 1)
			return True

	def _log_upload_skipped_reason(self, results: List[TestResult], logger):
		"""Log detailed reason why upload was skipped"""
		logger.log('\nData Upload Status:', 1)
		logger.log('=' * 30, 1)
		logger.log('Upload SKIPPED due to test execution issues', 2)
		
		# Analyze and report the reasons
		status_counts = {}
		for result in results:
			status_counts[result.status] = status_counts.get(result.status, 0) + 1
		
		total_tests = len(results)
		
		logger.log('Reason Analysis:', 2)
		if 'CANCELLED' in status_counts:
			cancelled_count = status_counts['CANCELLED']
			logger.log(f'- {cancelled_count}/{total_tests} tests were cancelled by user', 2)
		
		if 'ExecutionFAIL' in status_counts:
			exec_fail_count = status_counts['ExecutionFAIL']
			logger.log(f'- {exec_fail_count}/{total_tests} tests had execution failures', 2)
		
		# Check if series was incomplete
		if results and results[-1].status in {'CANCELLED', 'ExecutionFAIL'}:
			logger.log('- Test series ended prematurely due to critical failure', 2)
		
		logger.log('Data saved locally for debugging purposes only', 1)
		logger.log('No database upload performed', 1)

	def _log_test_statistics(self, results: List[TestResult], logger):
		"""Log detailed test statistics"""
		total_tests = len(results)
		if total_tests == 0:
			logger.log('No test results to analyze', 2)
			return
		
		# Count different result types
		status_counts = {}
		for result in results:
			status_counts[result.status] = status_counts.get(result.status, 0) + 1
		
		logger.log('\nTest Execution Statistics:', 1)
		logger.log('=' * 40, 1)
		logger.log(f'Total Tests Executed: {total_tests}', 1)
		
		for status, count in status_counts.items():
			percentage = (count / total_tests) * 100
			logger.log(f'{status}: {count} ({percentage:.1f}%)', 1)
		
		# Calculate success rate (excluding cancelled and execution failures)
		valid_tests = total_tests - status_counts.get('CANCELLED', 0) - status_counts.get('ExecutionFAIL', 0)
		if valid_tests > 0:
			passed_tests = status_counts.get('PASS', 0) + status_counts.get('*', 0)  # Handle both PASS and * statuses
			success_rate = (passed_tests / valid_tests) * 100
			logger.log(f'Success Rate (valid tests): {success_rate:.1f}%', 1)

	# ==================== STRATEGIES ==================

	def Loops(self, loops: int = 5, **config_updates) -> List[str]:
		"""Run loop test"""
		self.update_configuration(**config_updates)
		
		# Update unit data
		# self.update_unit_data()
		
		strategy = LoopTestStrategy(loops)
		return self._execute_strategy_and_process_results(strategy, "Loops")
	
	def Sweep(self, ttype: str = 'frequency', domain: str = 'ia', start: float = 16, 
			  end: float = 39, step: float = 4, **config_updates) -> List[str]:
		"""Run sweep test"""
		self.update_configuration(**config_updates)
		
		# Update unit data
		# self.update_unit_data()
		
		strategy = SweepTestStrategy(ttype, domain, start, end, step)
		return self._execute_strategy_and_process_results(strategy, "Sweep")
	
	def Shmoo(self, file: str = r'C:\Temp\ShmooData.json', label: str = 'COREFIX', 
			  **config_updates) -> List[str]:
		"""Run shmoo test"""
		self.update_configuration(**config_updates)
		
		# Update unit data
		# self.update_unit_data()
		
		# Load shmoo configuration
		shmoo_data = dpm.dev_dict(file, False)[label]
		
		# Update configuration from shmoo file
		volt_settings = shmoo_data['VoltageSettings']
		freq_settings = shmoo_data['FrequencySettings']
		
		self.update_configuration(
			volt_type=volt_settings['Type'],
			volt_IA=volt_settings['core'],
			volt_CFC=volt_settings['cfc'],
			freq_ia=freq_settings['core'],
			freq_cfc=freq_settings['cfc']
		)
		
		strategy = ShmooTestStrategy(shmoo_data['Xaxis'], shmoo_data['Yaxis'])
		return self._execute_strategy_and_process_results(strategy, "Shmoo")
	
	def _setup_strategy_environment(self) -> Dict:
		"""Setup environment once per strategy execution"""
		# Create test folder for the entire strategy
		description = f'T{self.config.tnumber}_{self.config.name}'
		self.config.tfolder = fh.create_log_folder(logs_dest, description)
		
		# Copy TTL files once for the entire strategy and store them in config
		self._copy_ttl_files_to_config()
		Framework.FrameworkPrint(f"Strategy environment setup complete. Test folder: {self.config.tfolder}", 1)

	# ==================== MAIN EXECUTOR ==================

	def RecipeExecutor(self, data: Dict, S2T_BOOT_CONFIG: Dict = None, 
					  extmask: Dict = None, summary: bool = True, cancel_flag=None,
					  experiment_name: str = None) -> List[str]:
		"""Execute test from recipe data with proper dependency injection"""

		# IMPORTANT: Clear any previous END command state at the start
		self._reset_execution_state()
		
		# Store experiment name in config for status updates
		if experiment_name:
			self.config.experiment_name = experiment_name	

		if S2T_BOOT_CONFIG:
			# Update S2T configuration
			for key, value in S2T_BOOT_CONFIG.items():
				if hasattr(self.s2t_config, key):
					setattr(self.s2t_config, key, value)
		
		# Enables Cancellation checks during external S2T flows
		self.config.cancel_flag = cancel_flag

		# Update configuration from recipe
		config_mapping = ConfigurationMapping.CONFIG_MAPPING
		dragon_mapping = ConfigurationMapping.DRAGON_MAPPING
		linux_mapping = ConfigurationMapping.LINUX_MAPPING
		custom_mapping = ConfigurationMapping.CUSTOM_MAPPING

		config_updates = self.get_config_updates(data, config_mapping)

		dragon_updates = self.get_content_updates(data, dragon_mapping)
		linux_updates = self.get_content_updates(data, linux_mapping)
		custom_updates = self.get_content_updates(data, custom_mapping)

		if extmask:
			config_updates['extMask'] = extmask
	
		self.update_configuration(**config_updates)
		flow_type = self._get_current_flow_type()
		if self.config.content == ContentType.DRAGON:
			self.content_config = self.update_ttl_configuration(config_updates=dragon_updates, flow=flow_type)
		elif self.config.content == ContentType.LINUX:
			self.content_config = self.update_ttl_configuration(config_updates=linux_updates, flow=flow_type)
		elif self.config.content == ContentType.CUSTOM:
			self.content_config = self.update_ttl_configuration(config_updates=custom_updates, flow=flow_type)
		else:
			self.content_config = None

		# Parse TTL and create INI file if config is available
		if 'macro_folder' in config_updates and config_updates['macro_folder']:
			# Determine flow type from current configuration
			
			Framework.TTL_parse(
				folder=config_updates['macro_folder'], 
				config=self.content_config,
				flow_type=flow_type
			)
		else:
			Framework.FrameworkPrint("No macro folder specified, skipping TTL configuration", 2)

		# Execute based on test type
		test_type = data['Test Type']
		
		if test_type == 'Loops':
			return self.Loops(loops=data['Loops'])
		elif test_type == 'Sweep':
			return self.Sweep(
				ttype=data['Type'].lower(),
				domain=data['Domain'].lower(),
				start=data['Start'],
				end=data['End'],
				step=data['Steps']
			)
		elif test_type == 'Shmoo':
			return self.Shmoo(
				file=data['ShmooFile'],
				label=data['ShmooLabel']
			)
		else:
			raise ValueError(f"Unknown test type: {test_type}")
	
	# ==================== STATIC METHODS ==================

	@staticmethod
	def FrameworkPrint(text: str, level: int = None):
		"""Print framework messages with color coding"""
		RESET_COLOR = Fore.WHITE
		
		if level == 0:
			COLOR = Fore.YELLOW
		elif level == 1:
			COLOR = Fore.GREEN
		elif level == 2:
			COLOR = Fore.RED
		else:
			COLOR = Fore.WHITE
		
		print(COLOR + text + RESET_COLOR)
	
	@staticmethod
	def platform_check(com_port: str, ip_address: str):
		"""Check platform configuration"""
		TERATERM_PATH = ser.TERATERM_PATH
		TERATERM_RVP_PATH = ser.TERATERM_RVP_PATH
		TERATERM_INI_FILE = ser.TERATERM_INI_FILE
		
		fh.teraterm_check(
			com_port=com_port,
			ip_address=ip_address,
			teraterm_path=TERATERM_PATH,
			seteo_h_path=TERATERM_RVP_PATH,
			ini_file=TERATERM_INI_FILE,
			useparser=False,
			checkenv=True
		)
	
	@staticmethod
	def system_2_tester_default() -> Dict:
		"""Get default system to tester configuration"""
		return {
			'AFTER_MRC_POST': 0xbf000000,
			'EFI_POST': 0xef0000ff,
			'LINUX_POST': 0x58000000,
			'BOOTSCRIPT_RETRY_TIMES': 3,
			'BOOTSCRIPT_RETRY_DELAY': 60,
			'MRC_POSTCODE_WT': 30,
			'EFI_POSTCODE_WT': 60,
			'MRC_POSTCODE_CHECK_COUNT': 5,
			'EFI_POSTCODE_CHECK_COUNT': 10,
			'BOOT_STOP_POSTCODE': 0x0,
			'BOOT_POSTCODE_WT': 30,
			'BOOT_POSTCODE_CHECK_COUNT': 10
		}
	
	@staticmethod
	def Recipes(path: str = r'C:\Temp\DebugFrameworkTemplate.xlsx') -> Dict:
		"""Load recipes from file"""
		if path.endswith('.json'):
			data_from_sheets = fh.load_json_file(path)
		elif path.endswith('.xlsx'):
			data_from_sheets = fh.process_excel_file(path)
		else:
			return None
		
		tabulated_df = fh.create_tabulated_format(data_from_sheets)
		data_table = tabulate(tabulated_df, headers='keys', tablefmt='grid', showindex=False)
		print(data_table)
		
		return data_from_sheets
	
	@staticmethod
	def RecipeLoader(data: Dict, extmask: Dict = None, summary: bool = True, 
					skip: List[str] = [], upload_to_database: bool = True, update_unit_data = True):
		"""Load and execute multiple recipes"""
		framework = Framework(upload_to_database=upload_to_database)
		
		if update_unit_data: framework.update_unit_data()
		
		for sheet_name, recipe_data in data.items():
			if sheet_name in skip:
				Framework.FrameworkPrint(f'-- Skipping: {sheet_name}', 0)
				continue
			
			if recipe_data.get('Experiment') == 'Enabled':
				Framework.FrameworkPrint(f'-- Executing {sheet_name} --', 1)
				
				for field, value in recipe_data.items():
					Framework.FrameworkPrint(f"{field} :: {value}", 1)
				
				framework.RecipeExecutor(
					data=recipe_data,
					extmask=extmask,
					summary=summary
				)
	
	@staticmethod
	def Test_Macros_UI(root=None, data=None):
		"""Run TTL macro UI"""
		ser.run_ttl(root, data)
	
	@staticmethod
	def TTL_Test(visual: str, cmds: Dict, bucket: str = 'Dummy', 
				test: str = 'TTL Macro Validation', chkcore: int = None, 
				ttime: int = 30, tnum: int = 1, content: str = 'Dragon', 
				host: str = '192.168.0.2', PassString: str = 'Test Complete', 
				FailString: str = 'Test Failed', cancel_flag=False):
		"""Run TTL test"""
		qdf = dpm.qdf_str()
		
		ser.start(
			visual=visual,
			qdf=qdf,
			bucket=bucket,
			content=content,
			chkcore=chkcore,
			host=host,
			cmds=cmds,
			test=test,
			ttime=ttime,
			tnum=tnum,
			PassString=PassString,
			FailString=FailString,
			cancel_flag=cancel_flag
		)
	
	@staticmethod
	def TTL_parse(folder: str, config = None, flow_type = None):
		"""Parse TTL configuration and create/update INI file if config provided"""
		config_file = fh.create_path(folder, 'config.ini')
		converter = fh.FrameworkConfigConverter(config_file, logger=Framework.FrameworkPrint)
		
		if config != None and flow_type != None:
			Framework.FrameworkPrint(' -- Creating/Updating TTL Configuration File -- ', 1)

			dragon_config = None
			linux_config = None
			custom_config = None

			if isinstance(config, DragonConfiguration):
				dragon_config = config
			elif isinstance(config, LinuxConfiguration):
				linux_config = config
			else:
				Framework.FrameworkPrint(f' -- Unknown configuration type: {type(config)} -- ', 2)
			
			# Update/create the INI file
			success = converter.update_ini(
				dragon_config=dragon_config,
				linux_config=linux_config,
				flow_type=flow_type,
				command_timeout=9999999  # Default timeout
			)
			
			if success:
				Framework.FrameworkPrint(f' -- INI Configuration file updated: {config_file} -- ', 1)
			else:
				Framework.FrameworkPrint(' -- Failed to update INI configuration file -- ', 2)

		if converter.read_ini():
			converter.create_current_flow_csv(folder)
			config_data = converter.get_flow_config_data()
			Framework.FrameworkPrint(' -- TTL Test Configuration -- ')
			if config_data:
				table_data = [[key, value] for key, value in config_data.items()]
				data_table = tabulate(table_data, headers=["Parameter", "Value"], tablefmt="grid")
				Framework.FrameworkPrint(data_table)	
			
			else:
				Framework.FrameworkPrint(' -- Failed to read TTL configuration -- ', 2)	

	@staticmethod
	def get_unit_info() -> Dict:
		"""Get unit information"""
		return dpm.request_unit_info()
	
	@staticmethod
	def reboot_unit(waittime: int = 60, u600w: bool = False, wait_postcode: bool = False):
		"""Reboot unit"""
		if not u600w:
			dpm.powercycle(ports=[1])
		else:
			dpm.reset_600w()
			time.sleep(waittime)
		
		if wait_postcode:
			time.sleep(waittime)
			gcm._wait_for_post(gcm.EFI_POST, sleeptime=waittime)
			gcm.svStatus(refresh=True)
	
	@staticmethod
	def power_control(state: str = 'on', stime: int = 10):
		"""Control unit power"""
		if state == 'on':
			dpm.power_on(ports=[1])
		elif state == 'off':
			dpm.power_off(ports=[1])
		elif state == 'cycle':
			dpm.powercycle(stime=stime, ports=[1])
		else:
			Framework.FrameworkPrint('-- No valid power configuration selected use: on, off or cycle', 2)
	
	@staticmethod
	def power_status() -> bool:
		"""Get power status"""
		try:
			return dpm.power_status()
		except:
			Framework.FrameworkPrint('Not able to determine power status, setting it as off by default.', 2)
			return False
	
	@staticmethod
	def refresh_ipc():
		"""Refresh IPC connection"""
		try:
			gcm.svStatus(refresh=True)
		except:
			Framework.FrameworkPrint('!!! Unable to refresh SV and Unlock IPC. Issues with your system..', 2)
	
	@staticmethod
	def reconnect_ipc():
		"""Reconnect IPC"""
		try:
			gcm.svStatus(checkipc=True, checksvcores=False, refresh=False, reconnect=True)
		except:
			Framework.FrameworkPrint('!!! Unable to execute ipc reconnect operation, check your system ipc connection status...', 2)
	
	@staticmethod
	def warm_reset(waittime: int = 60, wait_postcode: bool = False):
		"""Perform warm reset"""
		try:
			dpm.warm_reset()
		except:
			Framework.FrameworkPrint('Failed while performing a warm reset...', 2)
		
		if wait_postcode:
			time.sleep(waittime)
			gcm._wait_for_post(gcm.EFI_POST, sleeptime=waittime)
			gcm.svStatus(refresh=True)
	
	@staticmethod
	def Masks(basemask=None, root=None, callback=None):
		"""Create debug mask"""
		return DebugMask(basemask, root, callback)
	
	@staticmethod
	def read_current_mask() -> Dict:
		"""Read current mask configuration"""
		return dpm.fuses(rdFuses=True, sktnum=[0], printFuse=False)

	#@staticmethod
	#def clear_s2t_cancel_flag(logger=FrameworkPrint):
	#	gcm.clear_cancel_flag(logger)	

class FrameworkExternalAPI:
	"""External API interface for automation systems"""
	
	def __init__(self, framework: Framework):
		self.framework = framework
	
	def end_experiment(self) -> Dict:
		"""End current experiment gracefully (works in both modes)"""
		success = self.framework.end_experiment()
		return {
			'success': success,
			'message': 'End command sent - experiment will finish current iteration and stop' if success else 'No experiment running or failed to send end command',
			'state': self.framework.get_execution_state()
		}
	
	def continue_next_iteration(self) -> Dict:
		"""Continue to next iteration (step-by-step mode only)"""
		success = self.framework.step_continue()
		return {
			'success': success,
			'message': 'Continue command sent' if success else 'Failed to send continue command (check if step-by-step mode is enabled and waiting)',
			'state': self.framework.get_execution_state()
		}
	
	def cancel_experiment(self) -> Dict:
		"""Cancel experiment immediately"""
		self.framework.cancel_execution()
		return {
			'success': True,
			'message': 'Cancel command sent - experiment will stop immediately',
			'state': self.framework.get_execution_state()
		}
	
	def get_current_state(self) -> Dict:
		"""Get current execution state"""
		return self.framework.get_execution_state()
	
	def get_iteration_statistics(self) -> Dict:
		"""Get detailed statistics for decision making"""
		state = self.framework.get_execution_state()
		stats = state.get('current_stats', {})
		
		return {
			'total_completed': stats.get('total_completed', 0),
			'pass_rate': stats.get('pass_rate', 0.0),
			'fail_rate': stats.get('fail_rate', 0.0),
			'recent_trend': self._analyze_recent_trend(state.get('latest_results', [])),
			'recommendation': self._get_recommendation(stats),
			'end_requested': state.get('end_requested', False),
			'sufficient_data': self._has_sufficient_data(stats)
		}
	
	def _has_sufficient_data(self, stats: Dict) -> bool:
		"""Determine if we have sufficient data for decision making"""
		total = stats.get('total_completed', 0)
		pass_rate = stats.get('pass_rate', 0.0)
		
		# Consider data sufficient if:
		# 1. We have at least 10 iterations, OR
		# 2. We have at least 5 iterations with very high pass rate (>95%), OR
		# 3. We have at least 5 iterations with very low pass rate (<20%)
		
		if total >= 10:
			return True
		elif total >= 5:
			if pass_rate >= 95 or pass_rate <= 20:
				return True
		
		return False
	
	def _get_recommendation(self, stats: Dict) -> str:
		"""Get recommendation based on current statistics"""
		pass_rate = stats.get('pass_rate', 0.0)
		total = stats.get('total_completed', 0)
		
		if total < 3:
			return "continue"  # Need more data
		elif self._has_sufficient_data(stats):
			if pass_rate >= 90:
				return "sufficient_data_good"  # Can end with good results
			elif pass_rate <= 30:
				return "sufficient_data_poor"  # Can end with poor results
			else:
				return "continue"  # Mixed results, need more data
		elif pass_rate >= 95:
			return "trending_excellent"  # Very good trend
		elif pass_rate <= 20:
			return "trending_poor"  # Very poor trend
		else:
			return "continue"  # Normal operation
		
#########################################################
######		Miscelaneous code
#########################################################

def print_separator_box(direction='down'):
	arrow = 'v' if direction == 'down' else '+'  # Box drawing arrows
	separator_line = f'{"-"*50}{arrow}{"-"*50}'
	return separator_line
	#print(separator_line)

def print_custom_separator(text):
	total_length = 101
	text_length = len(text)
	side_length = (total_length - text_length) // 2
	separator_line = f'{"*" * side_length} {text} {"*" * side_length}'
	
	# Adjust if the total length is not exactly 101 due to integer division
	if len(separator_line) < total_length:
		separator_line += '*'
	
	return separator_line

def initscript():
	# Create base folder if it does not exist
	fh.create_folder_if_not_exists(base_folder)

	# Create TTL and Shmoos folders if they do not exist
	ttlf = fh.create_folder_if_not_exists(ttl_dest)
	shmf = fh.create_folder_if_not_exists(shmoos_dest)
	logsf = fh.create_folder_if_not_exists(logs_dest)

	if not ttlf: replace_files(ttl=True, shmoo=False, replace = True)
	if not shmf: replace_files(ttl=False, shmoo=True, replace = True)

	print('Operation completed.')

def replace_files(ttl, shmoo, replace = False):
	if replace: user_input = "Y"
	else: ""
	# Copy files to TTL and Shmoos folders
	if ttl:fh.copy_files(ttl_source, ttl_dest, uinput=user_input)
	if shmoo:fh.copy_files(shmoos_source, shmoos_dest, uinput=user_input)

#######################################################
########## 		Quick Access Framework Functions
#######################################################

def Recipes(path=r'C:\Temp\DebugFrameworkTemplate.xlsx'):
	
	data_from_sheets = Framework.Recipes(path)

	return data_from_sheets

def RecipeLoader(data, extmask = None, summary = True, skip = [], upload_to_database=True):
	
	Framework.RecipeLoader(data, extmask, summary, skip, upload_to_database)

#######################################################
########## 		User Interface Calls
#######################################################

def ControlPanel():
	fcp.run(Framework)

def TTLMacroTest():
	Framework.Test_Macros_UI()

#######################################################
########## 		Masking Script 
#######################################################

def DebugMask(basemask=None, root=None, callback = None):

	#masks, array = gcm.CheckMasks(readfuse = True, extMasks=None)
	die = dpm.product_str()
	masks = dpm.fuses(rdFuses = True, sktnum =[0], printFuse=False) if basemask == None else basemask

	# Checks for all configurations, the dpm fuses will return None if that die is non existing on the system product

	compute0_core_hex = str(masks["ia_compute_0"]) if masks["ia_compute_0"] != None else None
	compute0_cha_hex = str(masks["llc_compute_0"]) if masks["llc_compute_0"] != None else None
	compute1_core_hex = str(masks["ia_compute_1"]) if masks["ia_compute_1"] != None else None
	compute1_cha_hex = str(masks["llc_compute_1"]) if masks["llc_compute_1"] != None else None
	compute2_core_hex = str(masks["ia_compute_2"]) if masks["ia_compute_2"] != None else None
	compute2_cha_hex = str(masks["llc_compute_2"]) if masks["llc_compute_2"] != None else None

	newmask = gme.Masking(root, compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product = die.upper(), callback=callback)
	#editor = gme.SystemMaskEditor(compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product = die.upper())
	#newmask = editor.start()

	return newmask

def currentTime():
	# Define the GMT-6 timezone
	gmt_minus_6 = pytz.timezone('Etc/GMT+6')

	# Get the current time in GMT-6
	current_time_gmt_minus_6 = datetime.now(gmt_minus_6)

	# Print the current time in GMT-6
	print("Current time in GMT-6:", current_time_gmt_minus_6.strftime('%Y-%m-%d %H:%M:%S'))

	return current_time_gmt_minus_6

#######################################################
########## 		Initialization
#######################################################

initscript()



