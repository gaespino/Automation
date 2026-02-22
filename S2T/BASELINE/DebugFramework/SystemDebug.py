import time
import os, sys
import ipccli
import namednodes
import pandas as pd
import shutil
from tabulate import tabulate
from datetime import datetime
import pytz
import colorama
import weakref
import atexit
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
import importlib

# Append the Main Scripts Path
MAIN_PATH = os.path.abspath(os.path.dirname(__file__))
ROOT_PATH = os.path.abspath(os.path.join(MAIN_PATH, '..'))

sys.path.append(ROOT_PATH)

# Check for DEV path
DEV_MODE = 'users.gaespino.dev' in MAIN_PATH.replace('\\', '.')

import DebugFramework.SerialConnection as ser
import DebugFramework.FileHandler as fh
import DebugFramework.UI.ControlPanel as fcp
import DebugFramework.Automation_Flow.AutomationHandler as acp
import DebugFramework.ExecutionHandler.utils.ThreadsHandler as th


#from ExecutionHandler.utils.ThreadsHandler import execution_state, ExecutionCommand


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

USE_TEST_MODE_S2T = False

## Folders
script_dir = os.path.dirname(os.path.abspath(__file__))
base_folder = 'C:\\SystemDebug'
ttl_source = os.path.join(script_dir, 'TTL')
shmoos_source = os.path.join(script_dir, 'Shmoos')
ttl_dest = os.path.join(base_folder, 'TTL')
shmoos_dest = os.path.join(base_folder, 'Shmoos')
logs_dest = os.path.join(base_folder, 'Logs')

PYTHONSV_CONSOLE_LOG = r"C:\Temp\PythonSVLog.log"

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
######		Framework Utils
#########################################################

import DebugFramework.ExecutionHandler.utils.FrameworkUtils as fut
importlib.reload(fut)
FrameworkUtils = fut.FrameworkUtils

# Load modules from FrameworkUtils
#gcm = fut.gcm
#dpm = fut.dpm
#s2t = fut.s2t
#s2tutils = fut.s2tutils

# S2T scripts
if DEV_MODE:
	import S2T.CoreManipulation as gcm
	import S2T.dpmChecks as dpm
	import S2T.SetTesterRegs as s2t

	# Utils
	import S2T.Tools.utils as s2tutils

	importlib.reload(ser)
	importlib.reload(fh)
	importlib.reload(fcp)
	importlib.reload(s2tutils)
	importlib.reload(th)

else:
	# Paths -- Hardcoded for now
	# GNR/CWF = users.THR.PythonScripts.thr
	# DMR = users.THR.dmr_debug_utilities

	import users.gaespino.dev.S2T.CoreManipulation as gcm
	import users.gaespino.dev.S2T.dpmChecks as dpm
	import users.gaespino.dev.S2T.SetTesterRegs as s2t

	# Utils
	import users.gaespino.dev.S2T.Tools.utils as s2tutils

#########################################################
######		Interfaces
#########################################################

from DebugFramework.Interfaces.IFramework import IStatusReporter

#########################################################
######		Configurations
#########################################################

#from ExecutionHandler.Enums import ContentType, TestTarget, VoltageType, TestType
from DebugFramework.ExecutionHandler.Configurations import (DragonConfiguration, LinuxConfiguration,
											 ConfigurationMapping, TestConfiguration,
											 SystemToTesterConfig, TestResult, ContentType,
											 TestTarget, VoltageType, TestType, TestStatus)

ULX_CPU_DICT = {'GNR': 'GNR_B0',
		   'CWF': 'CWF -gsv',
		   'DMR': 'DMR'} # DMR APIC unlock is performed by MerlinX

class ContentValues(Enum):
	PRODUCT = s2t.config.SELECTED_PRODUCT
	ULX_CPU = ULX_CPU_DICT[PRODUCT]

#########################################################
######		Code Debug Logger
#########################################################

from DebugFramework.ExecutionHandler.utils.DebugLogger import (
	debug_log,
	set_global_debug_enabled,
	set_global_debug_file,
	is_debug_enabled,
	_global_debug_logger,
	)

#########################################################
######		Exception Handling -- WIP
#########################################################

from DebugFramework.ExecutionHandler.Exceptions import BootFailureType, TestExecutionError

#########################################################
######		Status Manager
#########################################################

from DebugFramework.ExecutionHandler.StatusManager import StatusEventType, StatusContext, StatusUpdateManager

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
		debug_log("Starting cancellation check", 1, "CANCELLATION_CHECK")
		command_result = self.framework._check_commands()
		debug_log(f"Command check result: {command_result}", 1, "COMMAND_RESULT")

		if command_result == "CANCELLED":  # [CHECK] Handle CANCELLED status
			debug_log("Processing CANCELLED command", 2, "CANCELLATION")
			self.gdflog.log("CANCEL command received - stopping execution", 2)
			self.config.execution_cancelled = True
			self.current_status = TestStatus.CANCELLED
			self.execution_state.set_state('execution_active', False)
			debug_log("Cancellation state set, execution marked inactive", 2, "STATE_CHANGE")
			return True

		if (hasattr(self.config, 'execution_cancelled') and
			self.config.execution_cancelled and
			command_result != "CONTINUE"):  # [CHECK] Allow retries to continue

			debug_log("Execution already cancelled, confirming stop", 2, "CANCELLATION")
			self.gdflog.log("Execution already cancelled - stopping immediately", 2)
			return True

			#raise InterruptedError("Execution cancelled")
		elif command_result == "END_REQUESTED":
			debug_log("END command detected, allowing current iteration to complete", 2, "END_COMMAND")
			self.gdflog.log("END command received - finishing current iteration", 2)
			# Don't raise exception, let iteration complete
			return False

		elif command_result == "ERROR":
			debug_log("Command processing error, marking execution as failed", 3, "COMMAND_ERROR")
			self.current_status = TestStatus.FAILED
			self.execution_state.set_state('execution_active', False)
			return True

		debug_log("No cancellation detected, continuing execution", 1, "CANCELLATION_CHECK")
		return False
			#raise InterruptedError("Command processing error")
		# PAUSED and CONTINUE are handled in framework._check_commands

	def _setup_test_environment(self):
		"""Setup test environment and logging"""
		# Test folder is already set up at strategy level in self.config.tfolder
		debug_log(f"Setting up test environment for iteration {self.config.tnumber}", 1, "SETUP")

		self.config.log_file = os.path.join(self.config.tfolder, 'DebugFrameworkLogger.log')
		self.config.ser_log_file = ser.log_file_path
		debug_log(f"Log files configured - Framework: {self.config.log_file}, Serial: {self.config.ser_log_file}", 1, "LOG_CONFIG")

		# Initialize loggers
		debug_log("Initializing framework loggers", 1, "LOGGER_INIT")
		self.gdflog = fh.FrameworkLogger(self.config.log_file, 'FrameworkLogger', console_output=True)
		self.pylog = fh.FrameworkLogger(PYTHONSV_CONSOLE_LOG, 'PythonSVLogger', pythonconsole=True)


		# Update system configuration
		debug_log("Updating global system configuration", 1, "CONFIG_UPDATE")
		self._update_system_config()
		debug_log("Test environment setup completed", 1, "SETUP")

	def _update_system_config(self):
		"""Update global system configuration"""
		debug_log("Starting global configuration update", 1, "GLOBAL_CONFIG")

		config_updates = [
			("AFTER_MRC_POST", self.s2t_config.AFTER_MRC_POST),
			("EFI_POST", self.s2t_config.EFI_POST),
			("LINUX_POST", self.s2t_config.LINUX_POST),
			("BOOTSCRIPT_RETRY_TIMES", self.s2t_config.BOOTSCRIPT_RETRY_TIMES),
			("BOOTSCRIPT_RETRY_DELAY", self.s2t_config.BOOTSCRIPT_RETRY_DELAY),
			("MRC_POSTCODE_WT", self.s2t_config.MRC_POSTCODE_WT),
			("EFI_POSTCODE_WT", self.s2t_config.EFI_POSTCODE_WT),
			("MRC_POSTCODE_CHECK_COUNT", self.s2t_config.MRC_POSTCODE_CHECK_COUNT),
			("EFI_POSTCODE_CHECK_COUNT", self.s2t_config.EFI_POSTCODE_CHECK_COUNT),
			("BOOT_STOP_POSTCODE", self.s2t_config.BOOT_STOP_POSTCODE),
			("BOOT_POSTCODE_WT", self.s2t_config.BOOT_POSTCODE_WT),
			("BOOT_POSTCODE_CHECK_COUNT", self.s2t_config.BOOT_POSTCODE_CHECK_COUNT)
		]

		for config_name, config_value in config_updates:
			setattr(gcm, config_name, config_value)
			debug_log(f"Updated {config_name} = {config_value}", 1, "CONFIG_SET")

		debug_log("Global configuration update completed", 1, "GLOBAL_CONFIG")

	def execute_single_test(self) -> TestResult:
		"""Execute a single test iteration"""
		debug_log(f"=== STARTING TEST ITERATION {self.config.tnumber} ===", 1, "TEST_START")

		try:
			# Set up context for Status Updates
			debug_log("Configuring status manager context", 1, "STATUS_SETUP")
			self.status_manager.update_context(
					experiment_name=getattr(self.config, 'experiment_name', self.config.name),
					strategy_type=getattr(self.config, 'strategy_type', 'Unknown'),
					test_name=self.config.name,
					current_iteration=self.config.tnumber
				)

			# Check cancellation at start
			if self._check_cancellation():
				debug_log("Test cancelled before execution start", 2, "EARLY_CANCELLATION")
				self.status_manager.send_update(StatusEventType.ITERATION_CANCELLED, status='CANCELLED')
				return TestResult(status="CANCELLED", name=self.config.name, iteration=self.config.tnumber)

			# Send iteration start notification (0% of iteration)
			debug_log("Sending iteration start notification", 1, "STATUS_UPDATE")
			self.status_manager.send_update(
					StatusEventType.ITERATION_START,
					status='Starting Test Iteration',
					progress_weight=0.0
				)

			debug_log("Starting test environment setup", 1, "SETUP")
			self._log_test_banner()

			# Kill Any previous Teraterm Process
			debug_log("Cleaning up previous TeraTerm processes", 1, "CLEANUP")
			ser.kill_process(process_name='ttermpro.exe', logger=self.gdflog.log)

			# Prepare test environment
			debug_log("Preparing test environment configuration", 1, "ENV_PREP")
			boot_logging = self.config.content == ContentType.BOOTBREAKS
			wait_postcode = not self.config.u600w
			debug_log(f"Boot logging enabled: {boot_logging}, Wait postcode: {wait_postcode}", 1, "BOOT_CONFIG")

			# Setup serial configuration
			debug_log("Setting up serial configuration", 1, "SERIAL_SETUP")
			exp_ttl_files_dict = self._get_ttl_files_from_config()
			test_name = self._generate_test_name()
			debug_log(f"Generated test name: {test_name}", 1, "TEST_NAME")

			# Send boot start notification (10% of iteration)
			debug_log("Sending boot start notification", 1, "STATUS_UPDATE")
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Starting Boot Process',
					progress_weight=0.05
				)

			debug_log("Initializing TeraTerm serial interface", 1, "SERIAL_INIT")
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
				debug_log("Starting boot logging for BOOTBREAKS content", 1, "BOOT_LOG")
				serial.boot_start()

			debug_log("Starting Python SV logging", 1, "PYTHON_LOG")
			self._start_python_logging()

			# Checks cancellation before boot
			if self._check_cancellation():
				debug_log("Cancellation detected before boot process", 2, "PRE_BOOT_CANCEL")
				self.status_manager.send_update(StatusEventType.ITERATION_CANCELLED, status='CANCELLED')
				return TestResult(status="CANCELLED", name=self.config.name, iteration=self.config.tnumber)

			# Execute test based on target
			debug_log("Starting boot execution by target", 1, "BOOT_EXEC")
			boot_ready = self._execute_test_by_target()
			debug_log(f"Boot execution completed, ready status: {boot_ready}", 1, "BOOT_RESULT")

			# Checks cancellation after boot
			if self._check_cancellation():
				debug_log("Cancellation detected after boot process", 2, "POST_BOOT_CANCEL")
				self.status_manager.send_update(StatusEventType.ITERATION_CANCELLED, status='CANCELLED')
				return TestResult(status="CANCELLED", name=self.config.name, iteration=self.config.tnumber)

			# Send test execution notification (50% of iteration)
			debug_log("Sending boot completion notification", 1, "STATUS_UPDATE")
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Boot Process Complete',
					progress_weight=0.30,
					boot_ready=boot_ready
				)

			# Execute custom script if provided
			if self.config.script_file:
				debug_log(f"Executing custom script: {self.config.script_file}", 1, "CUSTOM_SCRIPT")
				self.status_manager.send_update(
						StatusEventType.ITERATION_PROGRESS,
						status='Executing Custom Script',
						progress_weight=0.30
					)
				self._execute_custom_script(self.config.script_file)

			debug_log("Stopping Python SV logging", 1, "PYTHON_LOG")


			# Handle test completion
			# Send test execution notification (50% of iteration)
			debug_log("Starting test content execution", 1, "CONTENT_EXEC")
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Running Test Content',
					progress_weight=0.35
				)

			if self.config.content == ContentType.PYSVCONSOLE:
				debug_log("Executing PYSVCONSOLE content", 1, "CONTENT_TYPE")
				serial.PYSVconsole()
			elif self.config.content == ContentType.BOOTBREAKS:
				debug_log("Executing BOOTBREAKS content", 1, "CONTENT_TYPE")
				serial.boot_end()
			else:
				debug_log(f"Executing standard content: {self.config.content}", 1, "CONTENT_TYPE")
				serial.run()

			# Handle test completion (75% of iteration)
			debug_log("Test content execution completed", 1, "CONTENT_COMPLETE")
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Test Content Complete - Processing Results',
					progress_weight=0.90
				)

			# Execute custom script if provided
			if self.config.post_process:
				debug_log(f"Executing post-process script: {self.config.post_process}", 1, "POST_PROCESS")
				self.status_manager.send_update(
						StatusEventType.ITERATION_PROGRESS,
						status='Executing Post Process Script',
						progress_weight=0.90
					)
				self._execute_custom_script(self.config.post_process, post=True)

			# Process results
			debug_log("Processing test results", 1, "RESULT_PROCESS")
			result = self._process_test_results(serial, test_name, boot_ready)
			debug_log(f"Test result processed: {result.status}", 1, "RESULT_STATUS")

			if boot_ready:
				self.current_status = TestStatus.SUCCESS
				debug_log("Test marked as SUCCESS due to boot_ready=True", 1, "STATUS_UPDATE")
			else:
				self.current_status = TestStatus.FAILED
				debug_log("Test marked as FAILED due to boot_ready=False", 2, "STATUS_UPDATE")

			# Send iteration complete notification (100% of iteration)
			debug_log("Sending iteration complete notification", 1, "STATUS_UPDATE")
			self.status_manager.send_update(
					StatusEventType.ITERATION_COMPLETE,
					iteration=self.config.tnumber,
					status=result.status,
					scratchpad=result.scratchpad,
					seed=result.seed,
					progress_weight=1.0
				)
			self._stop_python_logging()
			debug_log(f"=== TEST ITERATION {self.config.tnumber} COMPLETED: {result.status} ===", 1, "TEST_COMPLETE")
			return result

		except KeyboardInterrupt:
			debug_log("Test interrupted by KeyboardInterrupt", 3, "INTERRUPTION")
			self.current_status = TestStatus.CANCELLED
			self.execution_state.set_state('execution_active', False)

			self.status_manager.send_update(
					StatusEventType.ITERATION_CANCELLED,
					status='CANCELLED'
				)
			return TestResult(status="CANCELLED", name=self.config.name, iteration=self.config.tnumber)

		except Exception as e:
			debug_log(f"Test execution failed with exception: {xformat(e)}", 3, "EXECUTION_ERROR")

			self.gdflog.log(f"Test execution failed: {xformat(e)}", 3)
			self.current_status = TestStatus.FAILED

			self.status_manager.send_update(
					StatusEventType.ITERATION_FAILED,
					status='FAILED',
					error=str(e)
				)
			return TestResult(status="FAILED", name=self.config.name, iteration=self.config.tnumber)
		finally:
			# Single Test cleanup
			exec_state = self.execution_state.get_state('execution_active')
			self.gdflog.log(" Single Test Execution ended: Execution State: {exec_state}", 1)
			debug_log(f"Test execution cleanup - execution_active: {exec_state}", 1, "CLEANUP")

	def _log_test_banner(self):
		"""Log test information banner"""
		debug_log("Generating test information banner", 1, "BANNER")
		self.gdflog.log(' -- Test Start --- ')
		self.gdflog.log(f' -- Debug Framework {self.config.name} --- ')
		self.gdflog.log(f' -- Performing test iteration {self.config.tnumber} with the following parameters: ')

		# Enhanced parameter logging with debug context
		debug_log(f"Test parameters - Visual: {self.config.visual}, QDF: {self.config.qdf}", 1, "TEST_PARAMS")
		debug_log(f"Frequency settings - Core: {self.config.freq_ia}, Mesh: {self.config.freq_cfc}", 1, "FREQ_PARAMS")
		debug_log(f"Voltage settings - Core: {self.config.volt_IA}, Mesh: {self.config.volt_CFC}", 1, "VOLT_PARAMS")


		# Log configuration details
		EMPTY_FIELDS = [None, 'None', '', ' ']
		#print(f'COnfiguration Mask = "{self.config.extMask}"')
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
		self.gdflog.log(f'\t > Dis 1 Core (Atomcore): {self.config.dis1CPM} ')
		self.gdflog.log(f'\t > Core Freq: {self.config.freq_ia} ')
		self.gdflog.log(f'\t > Core Voltage: {self.config.volt_IA} ')
		self.gdflog.log(f'\t > Mesh Freq: {self.config.freq_cfc} ')
		self.gdflog.log(f'\t > Mesh Voltage: {self.config.volt_CFC} ')
		self.gdflog.log(f'\t > Running Content: {self.config.content.value} ')
		self.gdflog.log(f'\t > Pass String: {self.config.passstring} ')
		self.gdflog.log(f'\t > Fail String: {self.config.failstring} ')

		debug_log("Test banner generation completed", 1, "BANNER")

	def _get_ttl_files_from_config(self) -> Dict:
		"""Get TTL files from configuration (already copied at strategy level)"""
		debug_log("Retrieving TTL files configuration", 1, "TTL_CONFIG")
		if self.config.ttl_files_dict:
			debug_log("Using pre-copied TTL files from strategy setup", 1, "TTL_SOURCE")

			if self.config.ttl_path:
				debug_log(f"TTL files location: {self.config.ttl_path}", 1, "TTL_PATH")
				self.gdflog.log(f"Using pre-copied TTL files from strategy setup at: {self.config.ttl_path}", 1)
			return self.config.ttl_files_dict
		else:
			# Fallback to default if no pre-copied files available
			debug_log("No pre-copied TTL files found, using default configuration", 2, "TTL_FALLBACK")
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
		debug_log(f"Starting test execution by target: {self.config.target}", 1, "TARGET_EXEC")

		boot_ready = False
		wait_postcode = not self.config.u600w

		if self._check_cancellation():
			debug_log("Cancellation detected before target execution", 2, "PRE_TARGET_CANCEL")
			return False

		# Retry state flag
		self._in_retry_state = False
		debug_log("Retry state initialized to False", 1, "RETRY_STATE")

		debug_log(f'Initial Boot Status: {"READY" if boot_ready else "NOT_READY"}', 1, "BOOT_STATUS")
		try:
			debug_log("Starting System2Tester flow execution", 1, "S2T_FLOW")
			self._execute_system2tester_flow()

			if self._check_cancellation():
				debug_log("Cancellation detected after S2T flow", 2, "POST_S2T_CANCEL")
				return False

			boot_ready = True
			debug_log("S2T flow completed successfully, boot marked as ready", 1, "S2T_SUCCESS")

		except KeyboardInterrupt:
			debug_log("S2T flow interrupted by KeyboardInterrupt", 3, "S2T_INTERRUPT")
			self.gdflog.log("Script interrupted by user. --- Exiting...",2)
			self.current_status = TestStatus.CANCELLED
			return False
		except InterruptedError:
			debug_log("S2T flow interrupted by InterruptedError", 3, "S2T_INTERRUPT")
			self.gdflog.log("Script interrupted by user. --- Exiting...",2)
			self.current_status = TestStatus.CANCELLED
			return False
		except SyntaxError as se:
			debug_log(f"Syntax error during S2T flow: {se}", 3, "S2T_SYNTAX_ERROR")
			self.gdflog.log(f'Boot Syntax Error: {xformat(se)} --- Exiting...', 4)
			self.current_status = TestStatus.FAILED
			return False
		except Exception as e:
			debug_log(f"S2T flow failed, entering retry logic: {xformat(e)}", 3, "S2T_RETRY")
			self.gdflog.log(f'Boot Failed with Exception {xformat(e)} --- Retrying...', 4)

			# Marks we are in retry State
			self._in_retry_state = True
			debug_log("Retry state activated", 2, "RETRY_STATE")

			if self._check_cancellation():
				debug_log("Cancellation detected during retry preparation", 2, "RETRY_CANCEL")
				return False

			# Send boot retry notification
			debug_log("Sending boot retry notification", 1, "RETRY_NOTIFY")
			self.status_manager.send_update(
					StatusEventType.ITERATION_PROGRESS,
					status='Boot Failed - Retrying',
					progress_weight=0.10
				)

			if 'RSP 10' in str(e) or 'regaccfail' in str(e):
				debug_log("RegAcc failure detected, performing power cycle", 2, "REGACC_RECOVERY")
				self.gdflog.log('PowerCycling Unit -- RegAcc Fail during previous Boot', 4)
				FrameworkUtils.reboot_unit(wait_postcode=wait_postcode)

			else:
				debug_log("General boot failure, performing standard reboot", 2, "STANDARD_RECOVERY")
				FrameworkUtils.reboot_unit(wait_postcode=wait_postcode)

			debug_log("Waiting 120 seconds for system stabilization", 1, "RECOVERY_WAIT")
			time.sleep(120)

			if self._check_cancellation():
				debug_log("Cancellation detected after recovery wait", 2, "POST_RECOVERY_CANCEL")
				return False

			debug_log("Retrying S2T flow after recovery", 1, "S2T_RETRY_EXEC")
			self._execute_system2tester_flow()

			# Remove the in retry state flag
			self._in_retry_state = False
			debug_log("Retry state cleared after successful recovery", 1, "RETRY_STATE")

			if self._check_cancellation():
				debug_log("Cancellation detected after retry completion", 2, "POST_RETRY_CANCEL")
				return False

			boot_ready = True
			debug_log("S2T retry completed successfully", 1, "RETRY_SUCCESS")
		finally:
			# [CHECK] Ensure retry state is cleared
			self._in_retry_state = False
			debug_log("Retry state cleared in finally block", 1, "RETRY_CLEANUP")

		debug_log(f'Final Boot Status: {"READY" if boot_ready else "NOT_READY"}', 1, "BOOT_STATUS")

		return boot_ready

	def _execute_system2tester_flow(self):
		debug_log("Starting System2Tester flow selection", 1, "S2T_FLOW_START")

		if USE_TEST_MODE_S2T:
			debug_log("Framework running in TEST MODE - simulating S2T flow", 2, "TEST_MODE")
			self.gdflog.log(' Framework in Test Mode ',2)
			if self._check_cancellation():
				debug_log("Cancellation detected during test mode simulation", 2, "TEST_MODE_CANCEL")
				return
			for i in range(30):
				debug_log(f'Test Mode simulation step {i+1}/30', 1, "TEST_MODE_SIM")
				self.gdflog.log(f' Framework in Test Mode: Test -- {i} ',2)
				if self._check_cancellation():
					debug_log(f"Cancellation detected at test mode step {i+1}", 2, "TEST_MODE_CANCEL")
					return
				time.sleep(1)

		elif self.config.target == TestTarget.MESH:
			debug_log("Executing MESH target S2T flow", 1, "MESH_FLOW")
			debug_log(f"MESH parameters - Core freq: {self.config.freq_ia}, Mesh freq: {self.config.freq_cfc}", 1, "MESH_PARAMS")
			s2t.MeshQuickTest(
					core_freq=self.config.freq_ia,
					mesh_freq=self.config.freq_cfc,
					vbump_core=self.config.volt_IA,
					vbump_mesh=self.config.volt_CFC,
					Reset=self.config.reset,
					Mask=self.config.mask,
					pseudo=self.config.pseudo,
					dis_1CPM=self.config.dis1CPM,
					dis_2CPM=self.config.dis2CPM,
					GUI=False,
					fastboot=self.config.fastboot,
					corelic=self.config.corelic,
					volttype=self.config.volt_type.value,
					debug=False,
					boot_postcode=(self.config.content == ContentType.BOOTBREAKS),
					extMask=self.config.extMask,
					external_fusefile=self.config.fusefile,
					u600w=self.config.u600w,
					execution_state=self.execution_state
				)
			debug_log("MESH S2T flow completed", 1, "MESH_COMPLETE")
		elif self.config.target == TestTarget.SLICE:
			debug_log("Executing SLICE target S2T flow", 1, "SLICE_FLOW")
			debug_log(f"SLICE parameters - Target core: {self.config.mask}, Core freq: {self.config.freq_ia}", 1, "SLICE_PARAMS")
			s2t.SliceQuickTest(
					Target_core=self.config.mask,
					core_freq=self.config.freq_ia,
					mesh_freq=self.config.freq_cfc,
					vbump_core=self.config.volt_IA,
					vbump_mesh=self.config.volt_CFC,
					Reset=self.config.reset,
					pseudo=False,
					dis_1CPM=self.config.dis1CPM,
					dis_2CPM=self.config.dis2CPM,
					GUI=False,
					fastboot=self.config.fastboot,
					corelic=self.config.corelic,
					volttype=self.config.volt_type.value,
					debug=False,
					boot_postcode=(self.config.content == ContentType.BOOTBREAKS),
					external_fusefile=self.config.fusefile,
					u600w=self.config.u600w,
					execution_state=self.execution_state
				)
			debug_log("SLICE S2T flow completed", 1, "SLICE_COMPLETE")

		debug_log("System2Tester flow execution finished", 1, "S2T_FLOW_END")

	def _execute_custom_script(self, script, post = False):
		"""Execute custom script if provided"""

		if post:
			debug_log(f"Executing post-process custom script: {script}", 1, "POST_SCRIPT")
			self.gdflog.log(f"Executing Custom script After test: {script}", 1)
			fh.execute_file(file_path=script, logger=self.gdflog.log)
			debug_log("Post-process script execution completed", 1, "POST_SCRIPT")
		else:
			if self.config.content == ContentType.BOOTBREAKS:
				debug_log(f"Executing custom script at boot breakpoint: {script}", 1, "BREAKPOINT_SCRIPT")
				self.gdflog.log(f"Executing Custom Script at Boot Breakpoint: {script}", 1)
			elif self.config.content == ContentType.PYSVCONSOLE:
				debug_log(f"Executing pre-test custom script: {script}", 1, "PRE_SCRIPT")
				self.gdflog.log(f"Executing Custom Pre-Test Script: {script}", 1)

			fh.execute_file(file_path=script, logger=self.gdflog.log)
			debug_log("Custom script execution completed", 1, "CUSTOM_SCRIPT")

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


		# Unit Specific Logs
		self.product_specific()

		# Log results
		self.gdflog.log(f'tdata_{self.config.tnumber}::{run_name}::{run_status}::{scratchpad}::{seed}')
		self.gdflog.log(print_custom_separator('Test iteration summary'))
		self.gdflog.log(f' -- Test Name: {run_name} --- ')
		self.gdflog.log(f' -- Test Result: {run_status} --- ')
		self.gdflog.log(' -- Test End --- ')

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

	def product_specific(self):
		try:
			if ContentValues.PRODUCT == 'CWF':
				dpm.hwls_miscompare(logger=self.gdflog.log)
		except Exception as e:
			self.gdflog.log(f"Error in product_specific log: {e}")

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
		self._product = s2t.config.SELECTED_PRODUCT

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

		def product_apic_config():
			if self._product == "DMR":
				target_cbb = dpm.get_cbb_index(self._core)
				apic_location = dpm.get_single_compute_apic_location(self._core)
				apic_cdie = f'{target_cbb} {apic_location}' # Will set variables 2 and 3 of NSH
			else:
				apic_cdie = dpm.get_compute_index(self._core)

			return apic_cdie

		if self._dragon_config == None:
			self.logger(">>> Dragon Configuration not selected",3)
			return None

		self.logger(">>> Generating Dragon TTL Configuration",1)
		if self._flow and self._flow.upper() == "SLICE" and self._core:
			apic_cdie = product_apic_config()
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
			if hasattr(config, key):
				setattr(config, key, value)
			debug_log(f"Configuration Updates: {key} -> {value}", 1, "CONFIGURATION")
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
		debug_log(f"Starting LOOPS strategy execution: {self.loops} iterations", 1, "STRATEGY_START")
		results = []
		fail_count = 0


		# [CHECK] Log initial state
		initial_state = halt_controller.execution_state.get_state('execution_active')
		debug_log(f"Strategy starting: execution_active = {initial_state}", 1, "EXECUTION_STATE")
		executor.gdflog.log(f"Strategy starting: execution_active = {initial_state}", 1)

		# We do need Framework object here is a must
		if halt_controller == None:
			debug_log("No halt controller provided - strategy cannot execute", 3, "STRATEGY_ERROR")
			return ["FAILED", executor.config.name, executor.config.tnumber]

		# Initialize execution state
		# Prepare for execution
		debug_log("Initializing execution state for loops strategy", 1, "STATE_INIT")
		halt_controller.execution_state.update_state(
				execution_active=True,
				total_iterations=self.loops,
				current_iteration=0,
				experiment_name=executor.config.name,
				waiting_for_step=False
			)

		# Store strategy type in config for status updates
		executor.config.strategy_type = 'Loops'
		debug_log("Strategy type set to 'Loops'", 1, "STRATEGY_CONFIG")

		# [CHECK] Log initial state
		initial_state = halt_controller.execution_state.get_state('execution_active')
		executor.gdflog.log(f"Strategy after execution update: execution_active = {initial_state}", 1)

		# Status Manager Context Update
		debug_log("Updating status manager context", 1, "STATUS_SETUP")
		halt_controller.status_manager.update_context(
			strategy_type='Loops',
			total_iterations=self.loops
		)

		try:
			for i in range(self.loops):
				debug_log(f"=== STARTING LOOP ITERATION {i+1}/{self.loops} ===", 1, "LOOP_START")
				executor.config.tnumber = i + 1

				# [CHECK] Log state before each iteration
				#pre_iteration_state = halt_controller.execution_state.get_state('execution_active')
				#executor.gdflog.log(f"Before iteration {i+1}: execution_active = {pre_iteration_state}", 1)

				# Update current iteration in state
				halt_controller.execution_state.set_state('current_iteration', i + 1)
				halt_controller.status_manager.update_context(current_iteration=i + 1)
				debug_log(f"Current iteration updated to {i+1}", 1, "ITERATION_UPDATE")

				# Check for commands before starting iteration
				debug_log("Checking for commands before iteration start", 1, "PRE_ITERATION_CHECK")


				if halt_controller.execution_state.should_stop():
					command_result = halt_controller._check_commands()

					if command_result == "CANCELLED":
						debug_log(f"CANCEL command received before iteration {i + 1}", 2, "PRE_ITERATION_CANCEL")
						executor.gdflog.log(f"CANCEL command received - stopping before iteration {i + 1}", 2)
						results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=i + 1))
						break
					elif command_result == "ERROR":
						debug_log(f"Command error before iteration {i + 1}", 3, "PRE_ITERATION_ERROR")
						executor.gdflog.log(f"Command processing error before iteration {i + 1}", 3)
						results.append(TestResult(status="FAILED", name=executor.config.name, iteration=i + 1))
						break

				# Send progress update
				debug_log(f"Sending progress update for iteration {i+1}", 1, "PROGRESS_UPDATE")
				halt_controller.status_manager.send_update(
						StatusEventType.STRATEGY_PROGRESS,
						progress_percent=round((i + 1) / self.loops * 100, 1),
						current_value=f"Loop {i + 1}/{self.loops}"
					)

				executor.gdflog.log(f'{print_separator_box(direction="down")}')
				executor.gdflog.log(print_custom_separator(f'Running Loop iteration: {i + 1}/{self.loops}'))

				# Execute Test
				debug_log(f"Executing single test for iteration {i+1}", 1, "TEST_EXEC")
				result = executor.execute_single_test()
				results.append(result)
				debug_log(f"Iteration {i+1} completed with status: {result.status}", 1, "ITERATION_RESULT")

				# [CHECK] Log state after each iteration
				#post_iteration_state = halt_controller.execution_state.get_state('execution_active')
				#executor.gdflog.log(f"After iteration {i+1}: execution_active = {post_iteration_state}", 1)

				# Check for cancellation and break immediately
				if result.status == TestStatus.CANCELLED.value:
					debug_log(f"Test cancelled at iteration {i + 1} - stopping strategy", 2, "ITERATION_CANCELLED")
					executor.gdflog.log(f"LOOPS: Strategy execution cancelled at iteration {i + 1}", 2)
					#results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=i + 1))
					break
				elif result.status == TestStatus.EXECUTION_FAIL.value:
					debug_log(f"Execution failure at iteration {i + 1} - stopping strategy", 3, "EXECUTION_FAIL")
					break
				elif result.status == TestStatus.PASS.value:
					debug_log(f"Test passed - reset on pass: {executor.config.resetonpass}", 1, "RESET_CONFIG")
					if executor.config.resetonpass:
						executor.config.reset = executor.config.resetonpass
					else:
						executor.config.reset = False

				else:
					executor.config.reset = True # Always reset if FAIL or any other condition
					debug_log("Test failed or other status - reset enabled", 1, "RESET_CONFIG")

				executor.gdflog.log(f'{print_separator_box(direction="up")}')

				# Check for commands after iteration completion
				debug_log("Checking for commands after iteration completion", 1, "POST_ITERATION_CHECK")
				#command_result = halt_controller._check_commands()

				if halt_controller.should_end_after_iteration():
					command_result = halt_controller._check_commands()
					debug_log(f"END command processed - stopping after iteration {i + 1}", 2, "END_AFTER_ITERATION")
					executor.gdflog.log(f"END command received - stopping after iteration {i + 1}", 2)

					# Send status update
					halt_controller.status_manager.send_update(
							StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
							completed_iterations=i + 1,
							reason='END command received after iteration completion',
							final_result=result.status
						)
					halt_controller.execution_state.acknowledge_command(ExecutionCommand.END_EXPERIMENT, f"Strategy ended after iteration {i}")
					break

				if halt_controller.execution_state.is_step_mode_enabled():
					# [CHECK] Log state before waiting
					debug_log(f"Step mode active - waiting for step command after iteration {i+1}", 1, "STEP_MODE_WAIT")
					#pre_wait_state = halt_controller.execution_state.get_state('execution_active')
					#executor.gdflog.log(f"Loops Strategy in Step Mode -- {i+1}:{self.loops}", 1)
					#executor.gdflog.log(f"Loops Strategy : execution_active = {pre_wait_state}", 1)

					halt_controller.execution_state.set_state('waiting_for_step', True)

					#exec_status = halt_controller.execution_state.get_state('execution_active')
					#executor.gdflog.log(f"Loops Strategy : execution_active = {exec_status}")
					command_result = halt_controller._check_commands()
					debug_log(f"Step mode command result: {command_result}", 1, "STEP_COMMAND_RESULT")
					executor.gdflog.log(f"Loops Strategy in Step Mode -- {i+1}:{self.loops} (waiting for command: {command_result})", 1)

					# Acknowledge the step continue command AFTER processing
					if command_result == "CONTINUE" and halt_controller.execution_state.has_command(ExecutionCommand.STEP_CONTINUE):
						debug_log("Step continue processed - moving to next iteration", 1, "STEP_CONTINUE_PROCESS")
						executor.gdflog.log("Step continue processed - moving to next iteration", 1)

					elif command_result == "END_REQUESTED":
						debug_log("END command received during step mode", 2, "STEP_END_REQUEST")
						executor.gdflog.log("Loops Received END command - completing strategy", 1)
						# Acknowledge end command
						if halt_controller.execution_state.has_command(ExecutionCommand.END_EXPERIMENT):
							halt_controller.status_manager.send_update(
									StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
									completed_iterations=i + 1,
									reason='Loops END command received during step mode (waiting for command)',
									final_result=result.status
								)
						break

					elif command_result == "CANCELLED":
						debug_log("CANCEL command received during step mode", 3, "STEP_CANCEL")
						executor.gdflog.log("Loops Received CANCEL command in step mode (wait) - stopping strategy", 2)
						results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=i + 1))
						break
				else:
					debug_log("Normal mode - continuing to next iteration", 1, "NORMAL_MODE")
					executor.gdflog.log(f'Loop Strategy in Normal Mode -- {i+1}:{self.loops}')

				time.sleep(10)  # Brief pause between iterations

		# Update execution state
		except InterruptedError:
			debug_log("Loop execution cancelled by InterruptedError", 2, "STRATEGY_INTERRUPTED")
			executor.gdflog.log("Loop execution cancelled", 2)
			# Cancelled result if not already added
			if not results or results[-1].status != TestStatus.CANCELLED.value:
				results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=executor.config.tnumber))

		except Exception as e:
			debug_log(f"Loop execution error: {e}", 3, "STRATEGY_ERROR")
			executor.gdflog.log(f"Loop execution error: {e}", 3)
		finally:
			debug_log("Finalizing loops strategy execution", 1, "STRATEGY_FINALIZE")
			# [CHECK] Log final state
			#final_state = halt_controller.execution_state.get_state('execution_active')
			#executor.gdflog.log(f"Strategy finishing: execution_active = {final_state}", 1)

			# Update execution state
			halt_controller.execution_state.set_state('execution_active', False)
			halt_controller.execution_state.set_state('waiting_for_step', False)

			# Send final summary
			final_stats = halt_controller._calculate_current_stats(results)
			debug_log(f"Final statistics calculated: {len(results)} total results", 1, "FINAL_STATS")
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
			debug_log(f"LOOPS strategy execution completed: {len(results)} results", 1, "STRATEGY_COMPLETE")

		return results

class SweepTestStrategy(TestStrategy):
	"""Strategy for sweep tests"""

	def __init__(self, ttype: str, domain: str, start: float, end: float, step: float):
		self.ttype = ttype
		self.domain = domain
		self.values = self._generate_range(start, end, step)

	def _generate_range(self, start: float, end: float, step: float) -> List[float]:
		"""Generate test values range"""
		# Reverse check --- ???

		if self.ttype == 'frequency':
			rng = []
			rng = list(range(int(start), int(end) + int(step), int(step)))
			# This is to avoid passing our end value
			if rng[-1] > end:
				rng[-1] = end
			return rng#list(range(int(start), int(end) + int(step), int(step)))
		elif self.ttype == 'voltage':
			values = []
			current = start
			while current <= end + step/2:  # Add small tolerance for float comparison
				values.append(round(current, 5))
				current += step

			# This is to avoid passing our end value
			if values[-1] > end:
				values[-1] = end

			return values
		else:
			raise ValueError(f"Invalid sweep type: {self.ttype}")

	def execute(self, executor: TestExecutor, halt_controller=None) -> List[TestResult]:
		results = []
		total_tests = len(self.values)

		debug_log(f"Starting SWEEP strategy execution: {total_tests} iterations", 1, "STRATEGY_START")
		debug_log(f"Sweep parameters - Type: {self.ttype}, Domain: {self.domain}, Values: {self.values}", 1, "SWEEP_CONFIG")

		# We do need Framework object here is a must
		if halt_controller == None:
			debug_log("No halt controller provided - sweep strategy cannot execute", 3, "STRATEGY_ERROR")
			return ["FAILED", executor.config.name, executor.config.tnumber]

		# Initialize execution state
		debug_log("Initializing execution state for sweep strategy", 1, "STATE_INIT")
		halt_controller.execution_state.update_state(
			execution_active=True,
			total_iterations=total_tests,
			current_iteration=0,
			experiment_name=executor.config.name,
			waiting_for_step=False
		)

		# Store strategy type in config for status updates
		executor.config.strategy_type = 'Sweep'
		debug_log("Strategy type set to 'Sweep'", 1, "STRATEGY_CONFIG")

		# Status Manager Context Update
		debug_log("Updating status manager context for sweep", 1, "STATUS_SETUP")
		halt_controller.status_manager.update_context(
				strategy_type='Sweep',
				total_iterations=total_tests
			)

		try:
			for i, value in enumerate(self.values):
				debug_log(f"=== STARTING SWEEP ITERATION {i+1}/{total_tests} ===", 1, "SWEEP_START")
				debug_log(f"Setting {self.domain} {self.ttype} to {value}", 1, "SWEEP_VALUE")

				executor.config.tnumber = i + 1
				self._update_config_value(executor.config, value)
				debug_log(f"Configuration updated for iteration {i+1}", 1, "CONFIG_UPDATE")

				# Update current iteration in state

				halt_controller.execution_state.set_state('current_iteration', i + 1)
				halt_controller.status_manager.update_context(current_iteration=i + 1)
				debug_log(f"Current iteration updated to {i+1}", 1, "ITERATION_UPDATE")

				# Check for commands before starting iteration
				debug_log("Checking for commands before sweep iteration start", 1, "PRE_ITERATION_CHECK")

				#command_result = halt_controller._check_commands()
				if halt_controller.execution_state.should_stop():
					command_result = halt_controller._check_commands()
					if command_result == "CANCELLED":
						debug_log(f"CANCEL command received before sweep iteration {i + 1}", 2, "PRE_ITERATION_CANCEL")
						executor.gdflog.log(f"CANCEL command received - stopping before iteration {i + 1}", 2)
						results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=i + 1))
						break
					elif command_result == "ERROR":
						debug_log(f"Command error before sweep iteration {i + 1}", 3, "PRE_ITERATION_ERROR")
						executor.gdflog.log(f"Command processing error before iteration {i + 1}", 3)
						results.append(TestResult(status="FAILED", name=executor.config.name, iteration=i + 1))
						break

				# Send progress update
				debug_log(f"Sending sweep progress update for iteration {i+1}", 1, "PROGRESS_UPDATE")
				halt_controller.status_manager.send_update(
						StatusEventType.STRATEGY_PROGRESS,
						progress_percent=round((i + 1) / total_tests * 100, 1),
						current_value=f"{self.domain}={value}"
					)

				executor.gdflog.log(f'{print_separator_box(direction="down")}')
				executor.gdflog.log(f'Running Sweep iteration: {i + 1}/{total_tests}, {self.domain}={value}')

				debug_log(f"Executing single test for sweep iteration {i+1}", 1, "TEST_EXEC")
				result = executor.execute_single_test()
				results.append(result)
				debug_log(f"Sweep iteration {i+1} completed with status: {result.status}", 1, "ITERATION_RESULT")

				# Check for cancellation and break immediately
				if result.status == TestStatus.CANCELLED.value:
					debug_log(f"Sweep test cancelled at iteration {i + 1} - stopping strategy", 2, "ITERATION_CANCELLED")
					executor.gdflog.log(f"SWEEP: Strategy execution cancelled at iteration {i + 1}", 2)
					#results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=i + 1))
					break
				elif result.status == TestStatus.EXECUTION_FAIL.value:
					debug_log(f"Sweep execution failure at iteration {i + 1} - stopping strategy", 3, "EXECUTION_FAIL")
					break
				elif result.status == TestStatus.PASS.value:
					executor.config.reset = executor.config.resetonpass
					debug_log(f"Sweep test passed - reset on pass: {executor.config.resetonpass}", 1, "RESET_CONFIG")
				else:
					executor.config.reset = True # Always reset if FAIL or any other condition
					debug_log("Sweep test failed or other status - reset enabled", 1, "RESET_CONFIG")

				executor.gdflog.log(f'{print_separator_box(direction="up")}')

				# Check for commands after iteration completion
				debug_log("Checking for commands after sweep iteration completion", 1, "POST_ITERATION_CHECK")
				#command_result = halt_controller._check_commands()

				if halt_controller.should_end_after_iteration():
					command_result = halt_controller._check_commands()
					debug_log(f"END command processed - stopping sweep after iteration {i + 1}", 2, "END_AFTER_ITERATION")
					executor.gdflog.log(f"END command received - stopping after iteration {i + 1}", 2)

					# Send status update
					if halt_controller.status_manager:
						halt_controller.status_manager.send_update(
							StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
							completed_iterations=i + 1,
							reason='Sweep END command received after iteration completion',
							final_result=result.status
						)
						halt_controller.execution_state.acknowledge_command(
								ExecutionCommand.END_EXPERIMENT,
								f"Strategy ended after iteration {i}"
							)
					break

				if halt_controller.execution_state.is_step_mode_enabled():
					debug_log(f"Step mode active - waiting for step command after sweep iteration {i+1}", 1, "STEP_MODE_WAIT")
					executor.gdflog.log(f'Sweep Strategy in Step Mode -- {i+1}:{total_tests}')
					halt_controller.execution_state.set_state('waiting_for_step', True)

					debug_log("Sweep strategy waiting for step command", 1, "STEP_WAIT")
					executor.gdflog.log(f"Sweep Strategy in Step Mode -- {i+1}:{total_tests} (waiting for command)", 1)

					command_result = halt_controller._check_commands()
					debug_log(f"Sweep step mode command result: {command_result}", 1, "STEP_COMMAND_RESULT")

					# Acknowledge the step continue command AFTER processing
					if command_result == "CONTINUE" and halt_controller.execution_state.has_command(ExecutionCommand.STEP_CONTINUE):
						debug_log("Sweep step continue processed - moving to next iteration", 1, "STEP_CONTINUE_PROCESS")
						executor.gdflog.log("Step continue processed - moving to next iteration", 1)

					elif command_result == "END_REQUESTED":
						debug_log("END command received during sweep step mode", 2, "STEP_END_REQUEST")
						executor.gdflog.log("Sweep Received END command - completing strategy", 1)
						# Acknowledge end command
						if halt_controller.execution_state.has_command(ExecutionCommand.END_EXPERIMENT):
							halt_controller.status_manager.send_update(
									StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
									completed_iterations=i + 1,
									reason='Sweep END command received during step mode (waiting for command)',
									final_result=result.status
								)

						break

					elif command_result == "CANCELLED":
						debug_log("CANCEL command received during sweep step mode", 3, "STEP_CANCEL")
						executor.gdflog.log("Sweep Received CANCEL command in step mdoe (wait) - stopping strategy", 2)
						results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=i + 1))
						break
				else:
					debug_log("Sweep normal mode - continuing to next iteration", 1, "NORMAL_MODE")
					executor.gdflog.log(f'Sweep Strategy in Normal Mode -- {i+1}:{total_tests}')

				debug_log("Brief pause between sweep iterations", 1, "ITERATION_PAUSE")
				time.sleep(3)

		except InterruptedError:
			debug_log("Sweep execution cancelled by InterruptedError", 2, "STRATEGY_INTERRUPTED")
			executor.gdflog.log("Sweep execution cancelled", 2)
			# Cancelled result if not already added
			if not results or results[-1].status != TestStatus.CANCELLED.value:
				results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=executor.config.tnumber))

		except Exception as e:
			debug_log(f"Sweep execution error: {e}", 3, "STRATEGY_ERROR")
			executor.gdflog.log(f"Sweep execution error: {e}", 3)
		finally:
			# Update execution state
			debug_log("Finalizing sweep strategy execution", 1, "STRATEGY_FINALIZE")
			halt_controller.execution_state.set_state('execution_active', False)
			halt_controller.execution_state.set_state('waiting_for_step', False)

			# Send final summary
			final_stats = halt_controller._calculate_current_stats(results)
			debug_log(f"Sweep final statistics calculated: {len(results)} total results", 1, "FINAL_STATS")
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

			debug_log(f"SWEEP strategy execution completed: {len(results)} results", 1, "STRATEGY_COMPLETE")

		return results

	def _update_config_value(self, config: TestConfiguration, value: float):
		"""Update configuration with new test value"""
		debug_log(f"Updating sweep configuration: {self.ttype} {self.domain} = {value}", 1, "CONFIG_UPDATE")

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

		debug_log("Sweep configuration update completed", 1, "CONFIG_UPDATE")

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

		rng = []

		if ttype == 'frequency':
			rng = list(range(int(start), int(end) + int(step), int(step)))

			if rng[-1] > end:
				rng[-1] = end
			return rng
		elif ttype == 'voltage':
			values = []
			current = start

			while current <= end + step/2:
				values.append(round(current, 5))
				current += step

			if values[-1] > end:
				values[-1] = end

			return values

	def execute(self, executor: TestExecutor, halt_controller=None) -> List[TestResult]:
		results = []
		iteration = 1
		total_tests = len(self.x_values) * len(self.y_values)

		debug_log(f"Starting SHMOO strategy execution: {total_tests} total iterations", 1, "STRATEGY_START")
		debug_log(f"Shmoo dimensions: {len(self.x_values)} x {len(self.y_values)} matrix", 1, "SHMOO_CONFIG")
		debug_log(f"X-axis: {self.x_config['Type']} {self.x_config['Domain']} = {self.x_values}", 1, "X_AXIS_CONFIG")
		debug_log(f"Y-axis: {self.y_config['Type']} {self.y_config['Domain']} = {self.y_values}", 1, "Y_AXIS_CONFIG")

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
					#
					if halt_controller.execution_state.should_stop():
						command_result = halt_controller._check_commands()
						if command_result == "CANCELLED":
							executor.gdflog.log(f"CANCEL command received - stopping before iteration {iteration}", 2)
							results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=iteration))
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

					#command_result = halt_controller._check_commands()

					# Debug logging
					#active_commands = halt_controller.execution_state.get_active_commands()
					#executor.gdflog.log(f"DEBUG: Active commands before check: {[cmd.name for cmd in active_commands]}", 1)

					#executor.gdflog.log(f"DEBUG: Command result: {command_result}", 1)

					if halt_controller.should_end_after_iteration():
						command_result = halt_controller._check_commands()
						executor.gdflog.log(f"END command received - stopping after iteration {iteration}", 2)

						# Send status update
						halt_controller.status_manager.send_update(
							StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
							completed_iterations=iteration,
							reason='END command received after iteration completion',
							final_result=result.status
						)
						halt_controller.execution_state.acknowledge_command(
							ExecutionCommand.END_EXPERIMENT,
							f"Strategy ended after iteration {iteration}"
						)
						break


					if halt_controller.execution_state.is_step_mode_enabled():
						executor.gdflog.log(f'Shmoo Strategy in Step Mode -- {iteration}:{total_tests}')
						#if i <= self.loops:  # Not the last iteration
						halt_controller.execution_state.set_state('waiting_for_step', True)

						executor.gdflog.log(f"Shmoo Strategy in Step Mode -- {iteration}:{total_tests} (waiting for command)", 1)

						command_result = halt_controller._check_commands()

						# Acknowledge the step continue command AFTER processing
						if command_result == "CONTINUE" and halt_controller.execution_state.has_command(ExecutionCommand.STEP_CONTINUE):
							executor.gdflog.log("Step continue processed - moving to next iteration", 1)
							#halt_controller.execution_state.acknowledge_command(
							#	ExecutionCommand.STEP_CONTINUE,
							#	"Step continue processed"
							#)

						elif command_result == "END_REQUESTED":
							executor.gdflog.log("Shmoo Received END command - completing strategy", 1)
							# Acknowledge end command
							if halt_controller.execution_state.has_command(ExecutionCommand.END_EXPERIMENT):
								halt_controller.status_manager.send_update(
										StatusEventType.EXPERIMENT_ENDED_BY_COMMAND,
										completed_iterations=iteration,
										reason='Shmoo END command received during step mode (waiting for command)',
										final_result=result.status
									)
								#halt_controller.execution_state.acknowledge_command(
								#	ExecutionCommand.END_EXPERIMENT,
								#	f"Strategy ended after iteration {iteration}"
								#)
							break

						elif command_result == "CANCELLED":
							executor.gdflog.log("Shmoo Received CANCEL command in step mode (wait) - stopping strategy", 2)
							results.append(TestResult(status="CANCELLED", name=executor.config.name, iteration=iteration))
							break
					else:
						executor.gdflog.log(f'Shmoo Strategy in Normal Mode -- {iteration}:{total_tests}')
					time.sleep(3)

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
		self.set_fresh_configs()

		# Debug logging starts DISABLED by default
		debug_log("Framework instance created (debug logging may be disabled)", 1, "FRAMEWORK_INIT")

		self.content_config = None
		self.unit_data = None
		self._current_strategy = None
		self._current_executor = None
		self.product = FrameworkUtils.get_selected_product()

		# CRITICAL: Use queue-based status reporting instead of direct callback
		self.status_manager = StatusUpdateManager(
			status_reporter=status_reporter,  # Your MainThreadHandler instance
			logger=FrameworkUtils.FrameworkPrint
		)

		# Disable Send Updates if Status reporter is not included
		if status_reporter == None:
			self.status_manager.disable()

		self._current_test_stats = {}

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
			'waiting_for_step': False,
			'waiting_for_command': False,
			'experiment_name': None,
			'end_requested': False
		}

		# TTL Flow
		self.flow_type = None

		# Only log if debug is enabled
		if is_debug_enabled():
			debug_log("Framework initialization completed", 1, "FRAMEWORK_INIT")

	# Sets all configurations to Default -- Used to start from clean state in multiple Experiments
	def set_fresh_configs(self):
		self.config = TestConfiguration()
		self.s2t_config = SystemToTesterConfig()
		self.dragon_content = DragonConfiguration()
		self.linux_content = LinuxConfiguration()
		self.config_refresh_required = False

	def set_status_manager(self, status_reporter):

		self.status_manager = StatusUpdateManager(
			status_reporter=status_reporter,  # Your MainThreadHandler instance
			logger=FrameworkUtils.FrameworkPrint
		)
		self.status_manager.enable()
		FrameworkUtils.FrameworkPrint(f'Setting Status Manager: {self.status_manager}',1)

	def set_execution_state(self, execution_state):
		self.execution_state = execution_state
		FrameworkUtils.FrameworkPrint(f'Setting Execution State: {execution_state}',1)

	# ==================== COMMAND INTERFACE METHODS ====================

	def end_experiment(self):
		"""End current experiment after current iteration completes"""
		if not self.execution_state.get_state('execution_active'):
			FrameworkUtils.FrameworkPrint("No experiment currently running", 2)
			return False

		def end_callback(response):
			FrameworkUtils.FrameworkPrint(f"End experiment acknowledged: {response}", 1)

		success = self.execution_state.end_experiment(callback=end_callback)
		if success:
			FrameworkUtils.FrameworkPrint("END EXPERIMENT command issued", 1)
			# Send status update through the status reporter
			self.status_manager.send_update(
				StatusEventType.EXPERIMENT_END_REQUESTED,
				message='Framework received End command - will complete current iteration and stop'
			)

		return success

	def halt_execution(self):
		"""Halt test execution after current iteration completes"""
		if not self.execution_state.get_state('execution_active'):
			FrameworkUtils.FrameworkPrint("No execution to halt", 2)
			return False

		def halt_callback(response):
			FrameworkUtils.FrameworkPrint(f"Halt acknowledged: {response}", 1)

		success = self.execution_state.pause(callback=halt_callback)
		if success:
			FrameworkUtils.FrameworkPrint("HALT command issued", 1)
			self.status_manager.send_update(StatusEventType.EXECUTION_HALTED)
		return success

	def continue_execution(self):
		"""Continue halted test execution"""
		if not self.execution_state.is_paused():
			FrameworkUtils.FrameworkPrint("No halted execution to continue", 2)
			return False

		def continue_callback(response):
			FrameworkUtils.FrameworkPrint(f"Continue acknowledged: {response}", 1)

		success = self.execution_state.resume(callback=continue_callback)
		if success:
			FrameworkUtils.FrameworkPrint("CONTINUE command issued", 1)
			self.status_manager.send_update(StatusEventType.EXECUTION_RESUMED)
		return success

	def cancel_execution(self):
		"""Cancel test execution"""
		def cancel_callback(response):
			FrameworkUtils.FrameworkPrint(f"Cancel acknowledged: {response}", 1)

		success = self.execution_state.cancel(callback=cancel_callback)
		if success:
			FrameworkUtils.FrameworkPrint("CANCEL command issued", 1)

		if hasattr(self.config, 'execution_cancelled'):
			self.config.execution_cancelled = True

		return success

	def enable_step_by_step_mode(self):
		"""Enable step-by-step execution mode"""
		success = self.execution_state.enable_step_mode()
		if success:
			FrameworkUtils.FrameworkPrint("Step-by-step mode enabled", 1)
			self.status_manager.send_update(
				StatusEventType.STEP_MODE_ENABLED,
				message='Step-by-step execution mode enabled'
			)
		return success

	def disable_step_by_step_mode(self):
		"""Disable step-by-step execution mode"""
		success = self.execution_state.disable_step_mode()
		if success:
			FrameworkUtils.FrameworkPrint("Step-by-step mode disabled", 1)
			self.status_manager.send_update(
				StatusEventType.STEP_MODE_DISABLED,
				message='Step-by-step execution mode disabled - switching to continuous mode'
			)
		return success

	def step_continue(self):
		"""Continue to next iteration in step-by-step mode"""
		if not self.execution_state.is_step_mode_enabled():
			FrameworkUtils.FrameworkPrint("Step-by-step mode is not enabled", 2)
			return False

		# FIXED: More lenient validation - allow some timing flexibility
		waiting_for_step = self.execution_state.get_state('waiting_for_step')
		execution_active = self.execution_state.get_state('execution_active')

		if not waiting_for_step and execution_active:
			FrameworkUtils.FrameworkPrint("Framework is active but not waiting for step - may be processing previous command", 1)
			# Give it a moment and try again
			time.sleep(0.5)
			waiting_for_step = self.execution_state.get_state('waiting_for_step')

		if not waiting_for_step:
			FrameworkUtils.FrameworkPrint("No iteration waiting for continue command", 2)
			return False

		def step_callback(response):
			FrameworkUtils.FrameworkPrint(f"Step continue acknowledged: {response}", 1)

		# Clear any previous persistent state
		self.execution_state.clear_persistent_command_state(ExecutionCommand.STEP_CONTINUE)

		success = self.execution_state.step_continue(callback=step_callback)
		if success:
			FrameworkUtils.FrameworkPrint("STEP CONTINUE command issued", 1)
			self.status_manager.send_update(StatusEventType.STEP_CONTINUE_ISSUED)

			# Set initial persistent state
			self.execution_state.set_persistent_command_state(
				ExecutionCommand.STEP_CONTINUE,
				'issued',
				{'issued_at': time.time()}
			)

		return success

	# ==================== COMMAND CHECKING METHODS ====================

	def _check_commands(self):
		"""Check and process commands (called from background thread)"""
		debug_log("Starting command check cycle", 1, "COMMAND_CHECK")
		try:
			# Check for cancellation FIRST (highest priority)
			if self.execution_state.is_cancelled():
				debug_log("CANCEL command detected - processing cancellation", 2, "CANCEL_PROCESS")
				self.execution_state.start_processing_command(ExecutionCommand.CANCEL)

				if self.execution_state.has_command(ExecutionCommand.EMERGENCY_STOP):
					debug_log("EMERGENCY_STOP command also detected", 3, "EMERGENCY_STOP")
					self.execution_state.start_processing_command(ExecutionCommand.EMERGENCY_STOP)

				# Set persistent cancellation state in config
				if hasattr(self, 'config'):
					self.config.execution_cancelled = True
					debug_log("Cancellation state set in config", 2, "CONFIG_UPDATE")

				return "CANCELLED"

			# Check for end experiment SECOND (allow current iteration to complete)
			if self.execution_state.is_ended():
				debug_log("END_EXPERIMENT command detected - processing end request", 2, "END_PROCESS")
				self.execution_state.start_processing_command(ExecutionCommand.END_EXPERIMENT)
				# Set persistent cancellation state in config
				if hasattr(self, 'config'):
					self.config.execution_ended = True
					debug_log("End experiment state set in config", 2, "CONFIG_UPDATE")


				return "END_REQUESTED"

			# Check for pause
			if self.execution_state.is_paused():
				debug_log("PAUSE command detected - handling pause", 1, "PAUSE_PROCESS")
				self._handle_pause_command()
				return "PAUSED"

			# Check for step continue in step mode
			if self.execution_state.is_step_mode_enabled():
				debug_log("Step mode enabled - checking step commands", 1, "STEP_CHECK")
				return self._handle_step_mode()

			debug_log("No active commands detected - continuing execution", 1, "COMMAND_CHECK")
			return "CONTINUE"

		except Exception as e:
			debug_log(f"Error during command check: {e}", 3, "COMMAND_ERROR")
			FrameworkUtils.FrameworkPrint(f"Error checking commands: {e}", 3)
			return "ERROR"

	def _handle_pause_command(self):
		"""Handle pause command"""
		self.execution_state.acknowledge_command(ExecutionCommand.PAUSE, "Execution paused")
		FrameworkUtils.FrameworkPrint("Execution paused - waiting for resume command", 1)

		# Wait for resume command
		while self.execution_state.is_paused():
			if self.execution_state.is_cancelled():
				raise InterruptedError("Cancelled while paused")
			time.sleep(0.1)  # Small delay to prevent busy waiting

		# Resume acknowledged
		self.execution_state.acknowledge_command(ExecutionCommand.RESUME, "Execution resumed")
		FrameworkUtils.FrameworkPrint("Execution resumed", 1)

	def _handle_step_mode(self):
		"""Handle step-by-step mode"""
		if self.execution_state.get_state('waiting_for_step'):
			debug_log("Framework waiting for step continue command", 1, "STEP_WAIT")
			FrameworkUtils.FrameworkPrint("Waiting for step continue command...", 1)
			max_wait_time = 60
			start_time = time.time()
			sleep_interval = 0.1
			max_sleep = 1
			last_log_time = start_time

			while True:
				# Check for step continue
				if self.execution_state.should_step_continue():
					debug_log("Step continue command received and validated", 1, "STEP_CONTINUE")
					FrameworkUtils.FrameworkPrint("Step continue command received - proceeding", 1)

					# IMMEDIATE ACKNOWLEDGMENT - before any other processing
					if self.execution_state.has_command(ExecutionCommand.STEP_CONTINUE):
						success = self.execution_state.acknowledge_command(
							ExecutionCommand.STEP_CONTINUE,
							"Step continue processed by framework"
						)
						debug_log(f"STEP_CONTINUE acknowledged: {success}", 1, "STEP_ACK")
						FrameworkUtils.FrameworkPrint(f"STEP_CONTINUE immediately acknowledged: {success}", 1)

					self.execution_state.set_state('waiting_for_step', False)
					debug_log("Step wait state cleared - proceeding with execution", 1, "STEP_PROCEED")
					return "CONTINUE"

				# Check for end experiment
				if self.execution_state.is_ended():
					debug_log("End experiment command received during step wait", 2, "STEP_END")
					FrameworkUtils.FrameworkPrint("End experiment command received - completing", 1)

					# IMMEDIATE ACKNOWLEDGMENT
					if self.execution_state.has_command(ExecutionCommand.END_EXPERIMENT):
						success = self.execution_state.acknowledge_command(
							ExecutionCommand.END_EXPERIMENT,
							"End experiment processed by framework"
						)
						debug_log(f"END_EXPERIMENT acknowledged: {success}", 1, "END_ACK")
						FrameworkUtils.FrameworkPrint(f"END_EXPERIMENT immediately acknowledged: {success}", 1)

					self.execution_state.set_state('waiting_for_step', False)
					debug_log("Step wait state cleared - proceeding with execution", 1, "STEP_END")
					return "END_REQUESTED"

				# Check for cancellation
				if self.execution_state.is_cancelled():
					debug_log("Cancel command received during step wait", 3, "STEP_CANCEL")
					FrameworkUtils.FrameworkPrint("Cancel command received - stopping", 2)

					# IMMEDIATE ACKNOWLEDGMENT
					if self.execution_state.has_command(ExecutionCommand.CANCEL):
						success = self.execution_state.acknowledge_command(
							ExecutionCommand.CANCEL,
							"Cancel processed by framework"
						)
						debug_log(f"CANCEL acknowledged: {success}", 1, "CANCEL_ACK")
						FrameworkUtils.FrameworkPrint(f"CANCEL immediately acknowledged: {success}", 1)

					self.execution_state.set_state('waiting_for_step', False)
					debug_log("Step wait state cleared - proceeding with execution", 1, "STEP_CANCEL")
					#raise InterruptedError("Cancelled while waiting for step")

				# Check for timeout
				elapsed = time.time() - start_time
				if elapsed > max_wait_time:
					debug_log(f"Step command wait timeout after {elapsed:.1f}s", 2, "STEP_TIMEOUT")
					FrameworkUtils.FrameworkPrint(f"Timeout waiting for step command after {elapsed:.1f}s", 2)
					self.execution_state.set_state('waiting_for_step', False)
					return "TIMEOUT"

				# [CHECK] Progressive sleep with periodic logging
				time.sleep(sleep_interval)
				sleep_interval = min(sleep_interval * 1.1, max_sleep)  # Gradually increase

				# Log every 30 seconds
				if elapsed - last_log_time >= 30:
					debug_log(f"Still waiting for step command - {elapsed:.0f}s elapsed", 1, "STEP_WAIT_UPDATE")
					FrameworkUtils.FrameworkPrint(f"Still waiting for command... ({elapsed:.0f}s elapsed)", 1)
					last_log_time = elapsed

		return "CONTINUE"

	def should_end_after_iteration(self) -> bool:
		"""Simple check if END command was issued - only call this at end of iterations"""
		return self.execution_state.has_command(ExecutionCommand.END_EXPERIMENT)

	# ==================== STATE MANAGEMENT ====================

	def _prepare_for_new_execution(self):
		"""Prepare framework for new execution"""
		debug_log("=== PREPARING FRAMEWORK FOR NEW EXECUTION ===", 1, "EXECUTION_PREP")

		try:
			debug_log("Starting framework preparation sequence", 1, "PREP_START")
			FrameworkUtils.FrameworkPrint("Preparing framework for new execution", 1)

			# Add a small delay to let any background command processing complete
			debug_log("Waiting for background command processing to complete", 1, "PREP_WAIT")
			time.sleep(0.2)

			# Reset execution state with force cleanup
			debug_log("Preparing execution state for new run", 1, "STATE_PREP")
			success = self.execution_state.prepare_for_execution()
			if not success:
				debug_log("Failed to prepare execution state", 3, "STATE_PREP_FAIL")
				FrameworkUtils.FrameworkPrint("Failed to prepare execution state", 3)
				return False

			# Double-check that commands are really cleared
			debug_log("Execution state prepared successfully", 1, "STATE_PREP_SUCCESS")
			active_commands = self.execution_state.get_active_commands()
			if active_commands:
				debug_log(f"WARNING: Commands still active after prepare: {[cmd.name for cmd in active_commands]}", 2, "ACTIVE_COMMANDS")
				FrameworkUtils.FrameworkPrint(f"WARNING: Commands still active after prepare: {[cmd.name for cmd in active_commands]}", 2)
				# Force clear them
				debug_log("Force clearing remaining active commands", 2, "FORCE_CLEAR")
				self.execution_state.clear_all_commands()

			# Reset framework-specific state
			debug_log("Resetting framework-specific execution state", 1, "FRAMEWORK_RESET")
			self._current_execution_state = {
				'is_running': False,
				'current_iteration': 0,
				'total_iterations': 0,
				'iteration_results': [],
				'current_stats': {},
				'waiting_for_step': False,
				'waiting_for_command': False,
				'experiment_name': None,
				'end_requested': False
			}

			# Send status update if reporter is available
			debug_log("Sending experiment prepared notification", 1, "STATUS_NOTIFY")
			self.status_manager.send_update(
				StatusEventType.EXPERIMENT_PREPARED,
				message='Framework prepared for new execution'
			)

			debug_log("Framework preparation completed successfully", 1, "PREP_SUCCESS")
			FrameworkUtils.FrameworkPrint("Framework prepared for new execution", 1)

			# Reset cancellation state
			if hasattr(self.config, 'execution_cancelled'):
				self.config.execution_cancelled = False
				debug_log("Cancellation state reset in config", 1, "CONFIG_RESET")

			# Reset end command state
			if hasattr(self.config, 'execution_ended'):
				self.config.execution_ended = False
				debug_log("End command state reset in config", 1, "CONFIG_RESET")

			debug_log("=== FRAMEWORK PREPARATION COMPLETED ===", 1, "EXECUTION_PREP")
			return True

		except Exception as e:
			debug_log(f"Error preparing for execution: {e}", 3, "PREP_ERROR")
			FrameworkUtils.FrameworkPrint(f"Error preparing for execution: {e}", 3)
			return False

	def _finalize_execution(self, reason="completed"):
		"""Finalize execution and cleanup"""
		debug_log(f"=== FINALIZING EXECUTION: {reason} ===", 1, "EXECUTION_FINALIZE")

		try:
			debug_log("Starting execution finalization process", 1, "FINALIZE_START")
			FrameworkUtils.FrameworkPrint(f"Finalizing execution: {reason}", 1)

			# Finalize execution state
			debug_log("Finalizing execution state", 1, "STATE_FINALIZE")
			self.execution_state.finalize_execution(reason)

			# Send final status
			if reason not in ["silent_cleanup_before_new_run", "cleanup_before_new_run"]:
				debug_log("Sending experiment finalized notification", 1, "STATUS_NOTIFY")
				self.status_manager.send_update(
					StatusEventType.EXPERIMENT_FINALIZED,
					reason=reason
				)
			else:
				debug_log(f"Skipping status notification for reason: {reason}", 1, "STATUS_SKIP")

			debug_log(f"Execution finalized successfully: {reason}", 1, "FINALIZE_SUCCESS")
			FrameworkUtils.FrameworkPrint(f"Execution finalized: {reason}", 1)

		except Exception as e:
			debug_log(f"Error finalizing execution: {e}", 3, "FINALIZE_ERROR")
			FrameworkUtils.FrameworkPrint(f"Error finalizing execution: {e}", 3)

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

		fail_count = status_counts.get('FAIL', 0)

		cancelled_count = status_counts.get('CANCELLED', 0)
		execution_fail_count = (status_counts.get('EXECUTIONFAIL', 0)+
								status_counts.get('FAILED', 0) +
								status_counts.get('ERROR', 0))

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
		debug_log("=== RESETTING EXECUTION STATE ===", 1, "STATE_RESET")

		try:
			debug_log("Starting execution state reset process", 1, "RESET_START")
			FrameworkUtils.FrameworkPrint("Resetting execution state for new run", 1)

			# Clear all active commands
			debug_log("Clearing all active commands", 1, "COMMAND_CLEAR")
			self.execution_state.clear_all_commands()

			# Refresh Configs --
			if self.config_refresh_required:
				debug_log("Config refresh required - setting fresh configurations", 1, "CONFIG_REFRESH")
				self.set_fresh_configs()

			# Reset execution state
			debug_log("Updating execution state to default values", 1, "STATE_UPDATE")
			self.execution_state.update_state(
				execution_active=False,
				current_experiment=None,
				current_iteration=0,
				total_iterations=0,
				waiting_for_step=False,
				framework_ready=True
			)


			# Reset any framework-specific state
			debug_log("Resetting framework-specific state", 1, "FRAMEWORK_STATE_RESET")
			self._current_execution_state = {
				'is_running': False,
				'current_iteration': 0,
				'total_iterations': 0,
				'iteration_results': [],
				'current_stats': {},
				'waiting_for_step': False,
				'waiting_for_command': False,
				'experiment_name': None,
				'end_requested': False
			}

			debug_log("Execution state reset completed successfully", 1, "RESET_SUCCESS")
			FrameworkUtils.FrameworkPrint("Execution state reset complete", 1)

		except Exception as e:
			debug_log(f"Error resetting execution state: {e}", 3, "RESET_ERROR")
			FrameworkUtils.FrameworkPrint(f"Error resetting execution state: {e}", 3)

	def get_step_mode_status(self) -> Dict:
		"""Get detailed step mode status information."""
		return {
			'step_mode_enabled': self.execution_state.is_step_mode_enabled(),
			'waiting_for_step': self.execution_state.get_state('waiting_for_step'),
			'current_iteration': self.execution_state.get_state('current_iteration'),
			'total_iterations': self.execution_state.get_state('total_iterations'),
			'execution_active': self.execution_state.get_state('execution_active')
		}

	def is_waiting_for_step_command(self) -> bool:
		"""Check if framework is waiting for a step command."""
		try:
			step_mode_enabled = self.execution_state.get_state('step_mode_enabled')
			waiting_for_step = self.execution_state.get_state('waiting_for_step')
			execution_active = self.execution_state.get_state('execution_active')

			result = step_mode_enabled and waiting_for_step and execution_active

			debug_log(f"Waiting for step command check: {result} (step_mode: {step_mode_enabled}, waiting: {waiting_for_step}, active: {execution_active})", 1, "STEP_WAIT_CHECK")

			return result

		except Exception as e:
			debug_log(f"Error checking step wait status: {e}", 3, "STEP_WAIT_ERROR")
			return False

	# ==================== EXECUTION METHODS ======================

	def _create_executor(self) -> TestExecutor:
		# [CHECK] Log state before creating executor
		pre_executor_state = self.execution_state.get_state('execution_active')
		FrameworkUtils.FrameworkPrint(f"State before creating executor: execution_active = {pre_executor_state}", 1)

		executor = TestExecutor(
			config=self.config,
			s2t_config=self.s2t_config,
			framework_instance=self
		)

		# [CHECK] Log state after creating executor
		post_executor_state = self.execution_state.get_state('execution_active')
		FrameworkUtils.FrameworkPrint(f"State after creating executor: execution_active = {post_executor_state}", 1)

		return executor

	def _execute_strategy_and_process_results(self, strategy: TestStrategy, test_type: str) -> List[str]:
		"""Execute strategy and process results"""


		# Store current thread reference
		with self._execution_thread_lock:
			self._execution_thread = threading.current_thread()

		try:
			self._current_strategy = strategy

			# Update execution state FIRST
			self.execution_state.update_state(
				execution_active=True,
				current_experiment=self.config.name,
				current_iteration=0,
				waiting_for_step=False
			)

			# Prepare for new execution
			if not self._prepare_for_new_execution():
				FrameworkUtils.FrameworkPrint("Failed to prepare for execution", 3)
				return ["FAILED"]

			# Get total iterations for this experiment
			total_iterations = self._get_strategy_total_iterations(strategy)
			self.execution_state.update_state(total_iterations=total_iterations)

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
			FrameworkUtils.FrameworkPrint(f"Setting up {test_type} test environment...", 1)
			self._setup_strategy_environment()

			# Create executor
			executor = self._create_executor()
			self._current_executor = executor

			# Define logging
			executor.gdflog.log(f"Starting {test_type} test execution...", 1)

			FrameworkUtils.FrameworkPrint(f"Starting {test_type} test execution...", 1)
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
			FrameworkUtils.FrameworkPrint(f"Error in strategy execution: {e}", 3)
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
		try:
			# Get actual state from execution_state handler
			execution_state_data = self.execution_state.get_full_state()
			actual_state = execution_state_data['state']

			# Get current statistics from status manager if available
			stats = {}
			if (hasattr(self, 'status_manager') and
				hasattr(self.status_manager, 'status_reporter') and
				hasattr(self.status_manager.status_reporter, 'state_machine')):
				try:
					stats = self.status_manager.status_reporter.state_machine.get_current_statistics()
				except Exception:
					stats = self._calculate_current_stats([])  # Fallback to empty stats
			else:
				stats = self._calculate_current_stats([])  # Fallback to empty stats

			# Get latest results from current executor if available
			latest_results = []
			if hasattr(self, '_current_execution_state') and self._current_execution_state.get('iteration_results'):
				latest_results = self._current_execution_state['iteration_results'][-5:]

			return {
				'execution_mode': self.config.execution_mode.value if hasattr(self.config, 'execution_mode') else 'continuous',
				'step_mode_enabled': actual_state.get('step_mode_enabled', False),  # FROM execution_state
				'is_running': actual_state.get('execution_active', False),  # FROM execution_state
				'waiting_for_command': self.is_waiting_for_step_command(),  # CALCULATED from actual state
				'waiting_for_step': actual_state.get('waiting_for_step', False),  # FROM execution_state
				'end_requested': self.execution_state.is_ended(),  # FROM execution_state method
				'current_iteration': actual_state.get('current_iteration', 0),  # FROM execution_state
				'total_iterations': actual_state.get('total_iterations', 0),  # FROM execution_state
				'experiment_name': actual_state.get('current_experiment', None),  # FROM execution_state
				'current_stats': stats,
				'latest_results': latest_results,
				'available_commands': self._get_available_commands()
			}

		except Exception as e:
			# Fallback to safe defaults if there's an error
			return {
				'execution_mode': 'continuous',
				'step_mode_enabled': False,
				'is_running': False,
				'waiting_for_command': False,
				'waiting_for_step': False,
				'end_requested': False,
				'current_iteration': 0,
				'total_iterations': 0,
				'experiment_name': None,
				'current_stats': {},
				'latest_results': [],
				'available_commands': [],
				'error': f'Failed to get execution state: {str(e)}'
			}

	def _get_available_commands(self) -> List[str]:
		"""Get list of available commands based on current state"""
		try:
			commands = []

			# Get actual state
			execution_active = self.execution_state.get_state('execution_active')
			step_mode_enabled = self.execution_state.get_state('step_mode_enabled')
			waiting_for_step = self.execution_state.get_state('waiting_for_step')
			is_paused = self.execution_state.is_paused()

			# Always available
			commands.append('get_execution_state')

			if execution_active:
				commands.extend(['end_experiment', 'cancel_execution'])

				if step_mode_enabled:
					if waiting_for_step:
						commands.append('step_continue')
					commands.append('disable_step_by_step_mode')
				else:
					commands.append('halt_execution')
					if is_paused:
						commands.append('continue_execution')
					commands.append('enable_step_by_step_mode')
			else:
				commands.append('enable_step_by_step_mode')

			return commands

		except Exception as e:
			return ['get_execution_state']  # Fallback to minimal commands

	def print_execution_status(self):
		"""Print current execution status"""
		status = self.get_execution_status()

		# Use executor logger if available, otherwise FrameworkPrint
		log_func = (self._current_executor.gdflog.log
				   if self._current_executor and hasattr(self._current_executor, 'gdflog')
				   else lambda msg, level: FrameworkUtils.FrameworkPrint(msg, level))

		log_func("=== EXECUTION STATUS ===", 1)
		log_func(f"Running: {status['is_running']}", 1)
		log_func(f"Mode: {status.get('execution_mode', 'continuous')}", 1)
		log_func(f"End Requested: {status.get('end_requested', False)}", 1)

		if self._step_mode_enabled:
			log_func("Step Mode: Enabled", 1)
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

	@staticmethod
	def RecipeLoader(data: Dict, extmask: Dict = None, summary: bool = True,
					skip: List[str] = [], upload_to_database: bool = True, update_unit_data = True):
		"""Load and execute multiple recipes"""
		framework = Framework(upload_to_database=upload_to_database)

		if update_unit_data: framework.update_unit_data()

		for sheet_name, recipe_data in data.items():
			if sheet_name in skip:
				FrameworkUtils.FrameworkPrint(f'-- Skipping: {sheet_name}', 0)
				continue

			if recipe_data.get('Experiment') == 'Enabled':
				FrameworkUtils.FrameworkPrint(f'-- Executing {sheet_name} --', 1)

				for field, value in recipe_data.items():
					FrameworkUtils.FrameworkPrint(f"{field} :: {value}", 1)

				framework.RecipeExecutor(
					data=recipe_data,
					extmask=extmask,
					summary=summary
				)

	# ==================== CONFIGURATION MANAGEMENT ==================

	def update_unit_data(self):
		"""Update unit data from system"""
		try:
			self.config.qdf = dpm.qdf_str()
			self.unit_data = dpm.request_unit_info()

			if self.unit_data:
				system_visual = self.unit_data.get('VISUAL_ID', [None])[0]
				if system_visual and self.config.visual != system_visual:
					FrameworkUtils.FrameworkPrint(f"Updating Visual ID: {self.config.visual} -> {system_visual}", 1)
					self.config.visual = system_visual

				self.config.data_bin = self.unit_data.get('DATA_BIN', [None])[0]
				self.config.data_bin_desc = self.unit_data.get('data_bin_desc', [None])[0]
				self.config.program = self.unit_data.get('PROGRAM', [None])[0]
		except Exception as e:
			FrameworkUtils.FrameworkPrint(f"Failed to update unit data: {xformat(e)}", 2)

	def _get_current_flow_type(self):
		"""Get current flow type based on framework configuration"""
		FrameworkUtils.FrameworkPrint(f'Selecting Flow Type for Content: {self.config.content}')
		if hasattr(self.config, 'content') and self.config.content == ContentType.LINUX:
			FrameworkUtils.FrameworkPrint('Linux Flow Selected')
			return "LINUX"
		elif hasattr(self.config, 'content') and self.config.content == ContentType.CUSTOM:
			FrameworkUtils.FrameworkPrint('Custom Flow Selected')
			return "CUSTOM"
		elif hasattr(self.config, 'target') and self.config.content == ContentType.DRAGON:
			if self.config.target == TestTarget.MESH:
				FrameworkUtils.FrameworkPrint('MESH Flow Selected')
				return "MESH"
			elif self.config.target == TestTarget.SLICE:
				FrameworkUtils.FrameworkPrint('SLICE Flow Selected')
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
				elif recipe_key == 'Disable 1 Core' and value:
					config_updates['dis1CPM'] = int(value, 16)
				elif recipe_key == 'Core License' and value:
					config_updates['corelic'] = int(value.split(":")[0])
				elif recipe_key == 'Test Mode' and value:
					config_updates['target'] = value.lower()
				elif recipe_key == 'Content' and value == ContentType.PYSVCONSOLE.value:
					conf_breakpoint = data.get('Boot Breakpoint', None)
					print(f"Content is {value}, checking Boot Breakpoint: {conf_breakpoint}")
					if conf_breakpoint:
						config_updates['content'] = ContentType.BOOTBREAKS.value
						print(f"Boot Breakpoint found, setting content to {config_updates['content']}")
				else:
					config_updates[config_key] = value

				debug_log(f"Configuration Updates: {recipe_key} -> {config_key} = {value}", 1, "CONFIGURATION")

		return config_updates

	def get_content_updates(self, data, config_mapping):

		config_updates = {}
		for recipe_key, config_key in config_mapping.items():
			#print(f'recipe_key {recipe_key} - {config_key}: Value - {data[recipe_key]}')
			if recipe_key in data and data[recipe_key] is not None:
				value = data[recipe_key]

				if recipe_key == 'Dragon Content Line' and value:
					config_updates['dragon_content_line'] = " ".join(s.strip() for s in value.split(","))
				elif recipe_key == 'Linux Pass String' and value == None:
					config_updates[config_key] = self.config.passstring
				elif recipe_key == 'Linux Fail String' and value == None:
					config_updates[config_key] = self.config.failstring
				else:
					config_updates[config_key] = value

				debug_log(f"Configuration Updates: {recipe_key} -> {config_key} = {value}", 1, "CONFIGURATION")

			# Linux Condtions to pass the Pass/fail string
			elif self.flow_type is not None and self.flow_type.lower() == 'linux' and recipe_key == 'Linux Pass String':
				config_updates[config_key] = self.config.passstring
				debug_log(f"Configuration Updates: {recipe_key} -> {config_key} = {self.config.passstring}", 1, "CONFIGURATION")
			elif self.flow_type is not None and self.flow_type.lower() == 'linux' and recipe_key == 'Linux Fail String':
				config_updates[config_key] = self.config.failstring
				debug_log(f"Configuration Updates: {recipe_key} -> {config_key} = {self.config.failstring}", 1, "CONFIGURATION")

		return config_updates

	def update_configuration(self, **kwargs):
		"""Update test configuration"""
		for key, value in kwargs.items():
			if hasattr(self.config, key):
				# Handle enum conversions

				if key == 'content' and isinstance(value, str):
					value = ContentType(value)
				elif key == 'target' and isinstance(value, str):
					value = TestTarget(value)
				elif key == 'volt_type' and isinstance(value, str):
					value = VoltageType(value)
				debug_log(f"Configuration Updates: {key} -> {value}", 1, "CONFIGURATION")
				setattr(self.config, key, value)

	def update_s2t_configuration(self, config_data: dict):
		"""Update S2T configuration"""
		# Updates the PostCode Break from the recipe data if exists
		print(f"Checking for postcode_break in config_data: {config_data}")
		if ('postcode_break' in config_data) and (config_data['postcode_break'] is not None):
			print(f"Updating S2T configuration with postcode_break: {config_data['postcode_break']}")
			try:
				if isinstance(config_data['postcode_break'], str):
					config_data['postcode_break'] = int(config_data['postcode_break'].strip(), 16)  # Remove any whitespace and convert to int
				self.s2t_config.BOOT_STOP_POSTCODE = config_data['postcode_break']
			except ValueError:
				print(f"Invalid postcode_break value: {config_data['postcode_break']}")

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
				pattern = f'{result.scratchpad}_{result.seed}'
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

			logger.log('\n2D Shmoo Plot Configuration:', 1)
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
			product = s2t.config.SELECTED_PRODUCT

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
			failed_tests = status_counts.get('FAIL', 0) + status_counts.get('*', 0)
			success_rate = (passed_tests / valid_tests) * 100
			repro_rate = (failed_tests / valid_tests) * 100
			logger.log(f'Pass Rate (valid tests): {success_rate:.1f}%', 1)
			logger.log(f'Fail Rate (valid tests): {repro_rate:.1f}%', 1)

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

		# [CHECK] Log state before setup
		pre_setup_state = self.execution_state.get_state('execution_active')
		FrameworkUtils.FrameworkPrint(f"State before environment setup: execution_active = {pre_setup_state}", 1)


		# Create test folder for the entire strategy
		description = f'T{self.config.tnumber}_{self.config.name}'
		self.config.tfolder = fh.create_log_folder(logs_dest, description)

		# Copy TTL files once for the entire strategy and store them in config
		self._copy_ttl_files_to_config()

		# [CHECK] Log state after setup
		post_setup_state = self.execution_state.get_state('execution_active')
		FrameworkUtils.FrameworkPrint(f"State after environment setup: execution_active = {post_setup_state}", 1)

		FrameworkUtils.FrameworkPrint(f"Strategy environment setup complete. Test folder: {self.config.tfolder}", 1)

	# ==================== MAIN EXECUTOR ==================

	def RecipeExecutor(self, data: Dict, S2T_BOOT_CONFIG: Dict = None,
					  extmask: Dict = None, summary: bool = True, cancel_flag=None,
					  experiment_name: str = None) -> List[str]:
		"""Execute test from recipe data with proper dependency injection"""

		# IMPORTANT: Clear any previous END command state at the start
		self._reset_execution_state()
		self.config_refresh_required = True

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

		if extmask:
			FrameworkUtils.FrameworkPrint(f' Updating External Mask to: {extmask}')
			config_updates['extMask'] = extmask

		# Handle Core Disable and Slice Disable lists from template
		coredislist = config_updates.get('coredislist')
		slicedislist = config_updates.get('slicedislist')
		if coredislist or slicedislist:
			# Use current extMask as base if already set, otherwise dpm.fuses() will be called inside
			base_mask = config_updates.get('extMask')
			if coredislist and str(coredislist).strip():
				core_list = [int(x.strip()) for x in str(coredislist).split(',') if x.strip().isdigit()]
				if core_list:
					FrameworkUtils.FrameworkPrint(f' Generating Core Disable Mask for cores: {core_list}')
					base_mask = gcm.generate_core_disable_mask(core_list, current_mask=base_mask)
			if slicedislist and str(slicedislist).strip():
				slice_list = [int(x.strip()) for x in str(slicedislist).split(',') if x.strip().isdigit()]
				if slice_list:
					FrameworkUtils.FrameworkPrint(f' Generating Slice Disable Mask for slices: {slice_list}')
					base_mask = gcm.generate_slice_disable_mask(slice_list, current_mask=base_mask)
			if base_mask is not None:
				FrameworkUtils.FrameworkPrint(f' External Mask after Core/Slice Disable: {base_mask}')
				config_updates['extMask'] = base_mask

		self.update_configuration(**config_updates)
		self.update_s2t_configuration(config_updates)

		self.flow_type = self._get_current_flow_type()

		dragon_updates = self.get_content_updates(data, dragon_mapping)
		linux_updates = self.get_content_updates(data, linux_mapping)
		custom_updates = self.get_content_updates(data, custom_mapping)


		if self.config.content == ContentType.DRAGON:
			self.content_config = self.update_ttl_configuration(config_updates=dragon_updates, flow=self.flow_type)
		elif self.config.content == ContentType.LINUX:
			self.content_config = self.update_ttl_configuration(config_updates=linux_updates, flow=self.flow_type)
		elif self.config.content == ContentType.CUSTOM:
			self.content_config = self.update_ttl_configuration(config_updates=custom_updates, flow=self.flow_type)
		else:
			self.content_config = None

		# Moving this to the Copy operation so we only edit the file at test location
		# Parse TTL and create INI file if config is available
		#if 'macro_folder' in config_updates and config_updates['macro_folder']:
		#	# Determine flow type from current configuration
		#	print(config_updates['macro_folder'])
		#	self.TTL_parse(
		#		folder=config_updates['macro_folder'],
		#		config=self.content_config,
		#		flow_type=flow_type
		#	)

		#else:
		#	FrameworkUtils.FrameworkPrint("No macro folder specified, skipping TTL configuration", 2)

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

	# ==================== TTL METHODS ==================

	def TTL_parse(self, folder: str, config = None, flow_type = None):
		"""Parse TTL configuration and create/update INI file if config provided"""
		config_file = fh.create_path(folder, 'config.ini')
		converter = fh.FrameworkConfigConverter(config_file, logger=FrameworkUtils.FrameworkPrint)

		if config != None and flow_type != None:
			FrameworkUtils.FrameworkPrint(' -- Creating/Updating TTL Configuration File -- ', 1)

			dragon_config = None
			linux_config = None
			custom_config = None

			if isinstance(config, DragonConfiguration):
				dragon_config = config
			elif isinstance(config, LinuxConfiguration):
				linux_config = config
			else:
				FrameworkUtils.FrameworkPrint(f' -- Unknown configuration type: {type(config)} -- ', 2)

			# Update/create the INI file
			success = converter.update_ini(
				dragon_config=dragon_config,
				linux_config=linux_config,
				flow_type=flow_type,
				command_timeout=9999999  # Default timeout
			)

			if success:
				FrameworkUtils.FrameworkPrint(f' -- INI Configuration file updated: {config_file} -- ', 1)
			else:
				FrameworkUtils.FrameworkPrint(' -- Failed to update INI configuration file -- ', 2)

		if converter.read_ini():
			converter.create_current_flow_csv(folder)
			config_data = converter.get_flow_config_data()
			FrameworkUtils.FrameworkPrint(' -- TTL Test Configuration -- ')
			if config_data:
				table_data = [[key, value] for key, value in config_data.items()]
				data_table = tabulate(table_data, headers=["Parameter", "Value"], tablefmt="grid")
				FrameworkUtils.FrameworkPrint(data_table)

			else:
				FrameworkUtils.FrameworkPrint(' -- Failed to read TTL configuration -- ', 2)

	def update_ttl_configuration(self, config_updates, flow):

		content = TestContentBuilder(
								data=config_updates,
								   dragon_config=self.dragon_content,
								   linux_config=self.linux_content,
								   custom_config=None,
								   logger = FrameworkUtils.FrameworkPrint,
								flow=flow,
								core=self.config.mask)

		return content.generate_ttl_configuration(self.config.content.value)

	def _copy_ttl_files_to_config(self) -> Dict:
		"""Copy TTL files once for the entire test strategy"""
		if not self.config.macro_folder:
			FrameworkUtils.FrameworkPrint("Using default TTL files (no macro folder specified)", 1)
			self.config.ttl_files_dict = macro_cmds
			self.config.ttl_path = ttl_dest # Default Value
			return   # Default TTL files

		FrameworkUtils.FrameworkPrint(f"Copying TTL files from: {self.config.macro_folder}", 1)

		replace = 'Y'
		self.config.ttl_path = fh.create_path(folder=self.config.tfolder, file='TTL')
		fh.create_folder_if_not_exists(self.config.ttl_path)
		fh.copy_files(self.config.macro_folder, self.config.ttl_path, uinput=replace)

		# Parsing TTL Directly into the Folder
		if self.content_config is not None and self.flow_type is not None:
			self.TTL_parse(
				folder=self.config.ttl_path,
				config=self.content_config,
				flow_type=self.flow_type
			)

		else:
			FrameworkUtils.FrameworkPrint("No Flow type or TTL 2.0 config version detected.", 2)

		self.config.ttl_files_dict = macros_path(self.config.ttl_path)
		FrameworkUtils.FrameworkPrint(f"TTL files copied to: {self.config.ttl_path}", 1)

class FrameworkExternalAPI:
	"""External API interface for automation systems"""

	# Class-level thread tracking for global cleanup
	_active_step_threads = weakref.WeakSet()
	_cleanup_registered = False

	def __init__(self, framework: Framework):
		self.framework = framework

		# Step-by-step specific attributes
		self._step_experiment_thread = None
		self._step_iteration_queue = None
		self._step_experiment_active = False
		self._step_thread_lock = threading.Lock()
		self._cleanup_event = threading.Event()  # Signal for graceful shutdown

		# Thread monitoring
		self._thread_monitor = None
		self._monitor_active = False

		# Status interceptor state
		self._original_send_update = None
		self._status_interceptor_active = False

		# Register global cleanup if not already done
		if not FrameworkExternalAPI._cleanup_registered:
			atexit.register(FrameworkExternalAPI._global_cleanup)
			FrameworkExternalAPI._cleanup_registered = True

	# ==================== STEP-BY-STEP EXPERIMENT METHODS ====================

	def start_experiment_step_by_step(self, experiment_data: Dict, experiment_name: str = None,
									 S2T_BOOT_CONFIG: Dict = None, extmask: Dict = None) -> Dict:
		"""
		Start experiment in step-by-step mode with comprehensive thread management.
		"""
		debug_log(f"=== STARTING STEP-BY-STEP EXPERIMENT: {experiment_name} ===", 1, "API_STEP_START")

		with self._step_thread_lock:
			try:
				debug_log("Acquiring step thread lock", 1, "THREAD_LOCK")

				# Cleanup any previous experiment first
				debug_log("Cleaning up any previous experiment", 1, "CLEANUP_PREV")
				self._cleanup_previous_experiment()

				# Check if another step experiment is running
				if self._step_experiment_active:
					debug_log("Another step experiment already running - rejecting request", 2, "EXPERIMENT_CONFLICT")
					return {
						'success': False,
						'error': 'Another step-by-step experiment is already running'
					}

				# Enable step-by-step mode first
				debug_log("Enabling step-by-step mode", 1, "STEP_MODE_ENABLE")
				step_mode_result = self.framework.enable_step_by_step_mode()
				if not step_mode_result:
					debug_log("Failed to enable step-by-step mode", 3, "STEP_MODE_FAIL")
					return {
						'success': False,
						'error': 'Failed to enable step-by-step mode'
					}

				debug_log("Step-by-step mode enabled successfully", 1, "STEP_MODE_SUCCESS")

				# Create communication queue for iteration events
				debug_log("Creating iteration event queue", 1, "QUEUE_CREATE")
				self._step_iteration_queue = queue.Queue(maxsize=0)
				self._step_experiment_active = True
				self._cleanup_event.clear()  # Reset cleanup event

				# Set up status interceptor
				debug_log("Setting up status interceptor", 1, "INTERCEPTOR_SETUP")
				self._setup_status_interceptor()

				def step_experiment_worker():
					"""Worker function with proper cleanup handling."""
					thread_name = threading.current_thread().name
					debug_log(f"Step experiment worker thread started: {thread_name}", 1, "WORKER_START")
					print(f"[{thread_name}] Starting step experiment thread for: {experiment_name}")

					try:
						# Check for cleanup signal before starting
						if self._cleanup_event.is_set():
							debug_log("Cleanup requested before experiment start", 2, "EARLY_CLEANUP")
							print(f"[{thread_name}] Cleanup requested before experiment start")
							return

						# Execute the experiment using existing RecipeExecutor
						debug_log("Starting recipe executor", 1, "RECIPE_START")
						final_results = self.framework.RecipeExecutor(
							data=experiment_data,
							S2T_BOOT_CONFIG=S2T_BOOT_CONFIG,
							experiment_name=experiment_name,
							extmask=extmask
						)

						debug_log(f"Recipe executor completed with {len(final_results)} results", 1, "RECIPE_COMPLETE")

						# Check for cleanup signal after experiment
						if self._cleanup_event.is_set():
							debug_log("Cleanup requested after experiment completion", 2, "POST_CLEANUP")
							print(f"[{thread_name}] Cleanup requested after experiment completion")
							return

						# Signal experiment completion
						debug_log("Preparing experiment completion event", 1, "COMPLETION_EVENT")
						completion_event = {
							'event_type': StatusEventType.EXPERIMENT_COMPLETE.value,
							'success': True,
							'final_results': final_results,
							'experiment_name': experiment_name,
							'timestamp': time.time(),
							'thread_name': thread_name
						}

						self._safe_queue_put(completion_event, "completion event")
						debug_log(f"Step experiment completed successfully: {experiment_name}", 1, "EXPERIMENT_SUCCESS")
						print(f"[{thread_name}] Step experiment completed successfully: {experiment_name}")

					except Exception as e:
						debug_log(f"Step experiment failed: {e}", 3, "EXPERIMENT_ERROR")
						print(f"[{thread_name}] Step experiment failed: {e}")

						# Signal experiment failure
						error_event = {
							'event_type': StatusEventType.EXPERIMENT_FAILED.value,
							'success': False,
							'error': str(e),
							'experiment_name': experiment_name,
							'timestamp': time.time(),
							'thread_name': thread_name
						}

						self._safe_queue_put(error_event, "error event")

					finally:
						debug_log("Step experiment worker thread finishing", 1, "WORKER_FINISH")
						print(f"[{thread_name}] Step experiment thread finishing")

						# Thread-level cleanup
						with self._step_thread_lock:
							self._step_experiment_active = False
							self._cleanup_status_interceptor()
							debug_log("Thread-level cleanup completed", 1, "THREAD_CLEANUP")

						# Signal thread completion
						completion_signal = {
							'event_type': StatusEventType.THREAD_COMPLETE.value,
							'thread_name': thread_name,
							'timestamp': time.time()
						}
						self._safe_queue_put(completion_signal, "thread completion signal")

						debug_log(f"Step experiment worker thread finished: {experiment_name}", 1, "WORKER_COMPLETE")
						print(f"[{thread_name}] Step experiment thread finished: {experiment_name}")

				# Start experiment in background thread
				debug_log("Creating step experiment thread", 1, "THREAD_CREATE")
				self._step_experiment_thread = threading.Thread(
					target=step_experiment_worker,
					name=f"StepExperiment_{experiment_name or 'Unknown'}_{int(time.time())}",
					daemon=False  # Don't use daemon - we want controlled cleanup
				)

				# Add to global tracking
				FrameworkExternalAPI._active_step_threads.add(self._step_experiment_thread)
				debug_log(f"Thread added to global tracking: {self._step_experiment_thread.name}", 1, "THREAD_TRACK")

				debug_log("Starting step experiment thread", 1, "THREAD_START")
				self._step_experiment_thread.start()

				# Start thread monitor
				debug_log("Starting thread monitor", 1, "MONITOR_START")
				self._start_thread_monitor()

				# Give the thread a moment to start
				time.sleep(0.5)

				debug_log(f"Step-by-step experiment started successfully: {experiment_name}", 1, "API_SUCCESS")
				return {
					'success': True,
					'message': f'Step-by-step experiment started: {experiment_name}',
					'experiment_name': experiment_name,
					'thread_id': self._step_experiment_thread.ident,
					'thread_name': self._step_experiment_thread.name,
					'step_mode_enabled': True
				}

			except Exception as e:
				# Cleanup on error
				debug_log(f"Failed to start step-by-step experiment: {e}", 3, "API_ERROR")
				self._force_cleanup_experiment()

				return {
					'success': False,
					'error': f'Failed to start step-by-step experiment: {str(e)}'
				}

	def wait_for_next_iteration_event(self, timeout: int = 60) -> Dict:
		"""
		Wait for the next iteration event with proper cleanup handling.
		"""
		debug_log(f"Waiting for next iteration event (timeout: {timeout}s)", 1, "API_WAIT_EVENT")

		try:
			if not self._step_iteration_queue:
				debug_log("No step iteration queue available", 2, "QUEUE_MISSING")
				return {
					'success': False,
					'error': 'No step-by-step experiment queue available'
				}

			# Check if cleanup was requested
			if self._cleanup_event.is_set():
				debug_log("Cleanup event detected during wait", 2, "CLEANUP_DETECTED")
				return {
					'success': False,
					'error': 'Experiment cleanup was requested',
					'cleanup_requested': True
				}

			# FIX: Use shorter timeout with retry logic for better responsiveness
			retry_timeout = min(timeout, 10) if timeout else 10
			start_time = time.time()
			debug_log(f"Starting event wait loop with retry timeout: {retry_timeout}s", 1, "WAIT_LOOP_START")

			while True:
				try:
					# Wait for next event with shorter timeout
					debug_log("Waiting for queue event", 1, "QUEUE_WAIT")
					event_data = self._step_iteration_queue.get(timeout=retry_timeout)

					debug_log(f"Received step event: {event_data['event_type']}", 1, "EVENT_RECEIVED")
					print(f"Received step event: {event_data['event_type']}")

					# Handle special events
					if event_data['event_type'] == StatusEventType.THREAD_COMPLETE.value:
						debug_log(f"Thread completion event received: {event_data.get('thread_name')}", 1, "THREAD_COMPLETE")
						print(f"Experiment thread completed: {event_data.get('thread_name')}")
						# Don't return this to client, wait for next event
						if timeout and (time.time() - start_time) >= timeout:
							debug_log("Overall timeout reached after thread completion", 2, "TIMEOUT_REACHED")
							return {
								'success': False,
								'error': f'No iteration event received within {timeout} seconds',
								'timeout': True
							}
						continue

					elif event_data['event_type'] == StatusEventType.THREAD_DIED.value:
						debug_log("Thread death event received", 3, "THREAD_DIED")
						return {
							'success': False,
							'error': 'Experiment thread died unexpectedly',
							'thread_died': True
						}

					debug_log("Returning valid event to client", 1, "EVENT_RETURN")
					return {
						'success': True,
						'event_data': event_data,
						'has_more_events': not self._step_iteration_queue.empty()
					}

				except queue.Empty:
					# Check if we've exceeded total timeout
					elapsed = time.time() - start_time
					debug_log(f"Queue timeout after {elapsed:.1f}s", 1, "QUEUE_TIMEOUT")

					if timeout and elapsed >= timeout:
						debug_log(f"Total timeout reached: {elapsed:.1f}s", 2, "TOTAL_TIMEOUT")
						return {
							'success': False,
							'error': f'No iteration event received within {timeout} seconds',
							'timeout': True
						}

					# Check if cleanup was requested during wait
					if self._cleanup_event.is_set():
						debug_log("Cleanup requested during queue wait", 2, "CLEANUP_DURING_WAIT")
						return {
							'success': False,
							'error': 'Experiment cleanup was requested during wait',
							'cleanup_requested': True
						}

					# Continue waiting if no timeout or timeout not reached
					if not timeout:
						debug_log("No timeout specified, continuing wait", 1, "CONTINUE_WAIT")
						continue

		except Exception as e:
			debug_log(f"Error waiting for iteration event: {e}", 3, "WAIT_ERROR")
			return {
				'success': False,
				'error': f'Error waiting for iteration event: {str(e)}'}

	# ==================== STATUS INTERCEPTOR METHODS ====================

	def _setup_status_interceptor(self):
		"""Set up interceptor to capture iteration completion events"""
		try:
			if self._status_interceptor_active:
				return

			if hasattr(self.framework.status_manager, 'send_update'):
				self._original_send_update = self.framework.status_manager.send_update

				def intercepted_send_update(event_type, **kwargs):
					"""Intercept status updates to capture iteration events."""
					try:
						# Call original method first
						result = self._original_send_update(event_type, **kwargs)

						if not self._step_experiment_active or self._cleanup_event.is_set():
							return result

						event_name = event_type.name if hasattr(event_type, 'name') else str(event_type)

						# [CHECK] Capture iteration completion with statistics from status handler
						if event_name == 'ITERATION_COMPLETE':
							# Get current statistics from the status handler
							current_stats = {}
							try:
								if hasattr(self.framework.status_manager, 'status_reporter'):
									state_machine = self.framework.status_manager.status_reporter.state_machine
									current_stats = state_machine.get_current_statistics()

							except Exception as e:
								print(f"Error getting statistics in interceptor: {e}")

							iteration_event = {
								'event_type': StatusEventType.ITERATION_COMPLETE.value,
								'success': True,
								'iteration': current_stats.get('current_iteration', 0),
								'status': kwargs.get('status', 'Unknown'),
								'status_classification': self._classify_test_status(kwargs.get('status', 'Unknown')),
								'scratchpad': kwargs.get('scratchpad', ''),
								'seed': kwargs.get('seed', ''),
								'progress_weight': kwargs.get('progress_weight', 0),
								'boot_ready': kwargs.get('boot_ready', False),
								'timestamp': time.time(),
								'statistics': current_stats,  # [CHECK] Include updated statistics from status handler
								'raw_kwargs': kwargs
							}

							self._safe_queue_put(iteration_event, f"iteration {iteration_event['iteration']} complete event")

						return result

					except Exception as e:
						print(f"Error in status interceptor: {e}")
						return self._original_send_update(event_type, **kwargs)

				self.framework.status_manager.send_update = intercepted_send_update
				self._status_interceptor_active = True
				print("Status interceptor set up successfully")

		except Exception as e:
			print(f"Failed to set up status interceptor: {e}")

	def _classify_test_status(self, status: str) -> Dict[str, bool]:
		"""
		Classify test status into categories for decision making.

		Returns:
			Dict with classification flags:
			- is_valid_test: True if PASS or FAIL (actual test results)
			- is_hardware_issue: True if hardware/system failure
			- should_continue: True if flow should continue
			- should_abort_flow: True if entire flow should be aborted
		"""
		status_upper = status.upper()

		# Valid test results (content passed or failed)
		if status_upper in [TestStatus.PASS.value, TestStatus.FAIL.value]:
			return {
				'is_valid_test': True,
				'is_hardware_issue': False,
				'should_continue': True,
				'should_abort_flow': False,
				'category': 'Valid Test'
			}

		# Hardware/System issues that should abort the flow
		elif status_upper in [TestStatus.EXECUTION_FAIL.value, TestStatus.FAILED.value, TestStatus.PYTHON_FAIL.value]:
			return {
				'is_valid_test': False,
				'is_hardware_issue': True,
				'should_continue': False,
				'should_abort_flow': True,
				'category': 'Test Error'
			}

		# User cancellation
		elif status_upper in [TestStatus.CANCELLED.value]:
			return {
				'is_valid_test': False,
				'is_hardware_issue': False,
				'should_continue': False,
				'should_abort_flow': True,
				'category': 'User Cancellation'
			}

		# Other statuses (SUCCESS, STARTED, etc.)
		else:
			return {
				'is_valid_test': False,
				'is_hardware_issue': False,
				'should_continue': True,
				'should_abort_flow': False,
				'category': 'Unknown'
			}

	def _cleanup_status_interceptor(self):
		"""
		Restore original status update method.
		"""
		try:
			if (self._status_interceptor_active and
				hasattr(self, '_original_send_update') and
				hasattr(self.framework.status_manager, 'send_update')):

				self.framework.status_manager.send_update = self._original_send_update
				self._original_send_update = None
				self._status_interceptor_active = False
				print("Status interceptor cleaned up")
		except Exception as e:
			print(f"Error cleaning up status interceptor: {e}")

	# ==================== THREAD MANAGEMENT METHODS ====================

	def _safe_queue_put(self, item, description="item"):
		"""Safely put item in queue with error handling."""
		if self._step_iteration_queue and not self._cleanup_event.is_set():
			try:
				self._step_iteration_queue.put(item, timeout=5)
				print(f"Queued {description}")
			except queue.Full:
				print(f"Warning: Failed to queue {description} - queue full")
			except Exception as e:
				print(f"Error queuing {description}: {e}")

	def _start_thread_monitor(self):
		"""Start a monitor thread to watch the experiment thread."""
		if self._thread_monitor and self._thread_monitor.is_alive():
			return  # Monitor already running

		def monitor_worker():
			monitor_name = threading.current_thread().name
			print(f"[{monitor_name}] Thread monitor started")

			consecutive_dead_checks = 0  # Counter for consecutive dead checks

			try:
				while self._monitor_active and not self._cleanup_event.is_set():
					if self._step_experiment_thread:
						# Check if we're in a retry state before declaring thread dead
						in_retry = getattr(self.framework._current_executor, '_in_retry_state', False)

						if not self._step_experiment_thread.is_alive() and not in_retry:
							consecutive_dead_checks += 1
							print(f"[{monitor_name}] Thread appears dead (check {consecutive_dead_checks}/3)")
							state =  self.get_current_state()

							if not state.get('is_running', False) and consecutive_dead_checks >= 5:
								print(f"[{monitor_name}] Experiment thread confirmed dead, cleaning up")
								self._handle_thread_death()
								break
							# Only trigger cleanup after multiple consecutive checks
							if consecutive_dead_checks >= 20:  # 6 seconds of being dead
								print(f"[{monitor_name}] Experiment thread confirmed dead, cleaning up")
								self._handle_thread_death()
								break
						elif in_retry:
							print(f"[{monitor_name}] Thread in retry state, skipping death check")
							consecutive_dead_checks = 0
						else:
							consecutive_dead_checks = 0  # Reset counter if thread is alive

					time.sleep(15)

			except Exception as e:
				print(f"[{monitor_name}] Thread monitor error: {e}")
			finally:
				print(f"[{monitor_name}] Thread monitor finished")

		self._monitor_active = True
		self._thread_monitor = threading.Thread(
			target=monitor_worker,
			name=f"StepMonitor_{int(time.time())}",
			daemon=True  # Monitor can be daemon
		)
		self._thread_monitor.start()

	def _handle_thread_death(self):
		"""Handle unexpected thread death."""
		print("Handling unexpected experiment thread death")

		# Signal thread death to waiting clients
		death_event = {
			'event_type': StatusEventType.THREAD_DIED.value,
			'timestamp': time.time(),
			'message': 'Experiment thread died unexpectedly'
		}
		self._safe_queue_put(death_event, "thread death event")

		# Force cleanup
		self._force_cleanup_experiment()

	# ==================== CLEANUP METHODS ====================

	def _cleanup_previous_experiment(self):
		"""Clean up any previous experiment resources."""
		try:
			if self._step_experiment_active or (self._step_experiment_thread and self._step_experiment_thread.is_alive()):
				print("Cleaning up previous step experiment")
				self._force_cleanup_experiment()
				time.sleep(1)  # Give cleanup time to complete
		except Exception as e:
			print(f"Error cleaning up previous experiment: {e}")

	def _force_cleanup_experiment(self):
		"""Force cleanup of experiment resources."""
		debug_log("=== FORCE CLEANUP EXPERIMENT ===", 1, "FORCE_CLEANUP")
		print("Force cleaning up step experiment")

		try:
			# Signal cleanup to all threads
			debug_log("Setting cleanup event signal", 1, "CLEANUP_SIGNAL")
			self._cleanup_event.set()

			# Stop monitor
			debug_log("Stopping thread monitor", 1, "MONITOR_STOP")
			self._monitor_active = False

			# Cleanup status interceptor
			debug_log("Cleaning up status interceptor", 1, "INTERCEPTOR_CLEANUP")
			self._cleanup_status_interceptor()

			# Clear queue
			if self._step_iteration_queue:
				debug_log("Clearing iteration event queue", 1, "QUEUE_CLEAR")
				queue_size = self._step_iteration_queue.qsize()
				while not self._step_iteration_queue.empty():
					try:
						self._step_iteration_queue.get_nowait()
					except queue.Empty:
						break
				debug_log(f"Cleared {queue_size} items from queue", 1, "QUEUE_CLEARED")

			# Wait for experiment thread to finish
			if self._step_experiment_thread and self._step_experiment_thread.is_alive():
				debug_log(f"Waiting for experiment thread to finish: {self._step_experiment_thread.name}", 1, "THREAD_WAIT")
				print(f"Waiting for experiment thread to finish: {self._step_experiment_thread.name}")

				# Try graceful shutdown first
				if hasattr(self.framework, 'cancel_execution'):
					debug_log("Sending cancel command for graceful shutdown", 1, "GRACEFUL_CANCEL")
					self.framework.cancel_execution()

				# Wait with timeout
				self._step_experiment_thread.join(timeout=10)

				if self._step_experiment_thread.is_alive():
					debug_log(f"Thread did not finish gracefully: {self._step_experiment_thread.name}", 2, "THREAD_STUCK")
					print(f"Warning: Experiment thread did not finish gracefully: {self._step_experiment_thread.name}")
					# Note: Cannot force kill thread in Python, but we can abandon it
				else:
					debug_log(f"Thread finished gracefully: {self._step_experiment_thread.name}", 1, "THREAD_FINISHED")
					print(f"Experiment thread finished gracefully: {self._step_experiment_thread.name}")

			# Wait for monitor thread to finish
			if self._thread_monitor and self._thread_monitor.is_alive():
				debug_log("Waiting for monitor thread to finish", 1, "MONITOR_WAIT")
				self._thread_monitor.join(timeout=5)

		except Exception as e:
			debug_log(f"Error during force cleanup: {e}", 3, "CLEANUP_ERROR")
			print(f"Error during force cleanup: {e}")
		finally:
			# Reset state
			debug_log("Resetting API state variables", 1, "STATE_RESET")
			self._step_experiment_active = False
			self._step_iteration_queue = None
			self._step_experiment_thread = None
			self._thread_monitor = None
			self._monitor_active = False

			debug_log("Force cleanup completed", 1, "CLEANUP_COMPLETE")
			print("Force cleanup completed")

	def cleanup_step_experiment(self):
		"""Public method for clean experiment cleanup."""
		with self._step_thread_lock:
			if self._step_experiment_active or (self._step_experiment_thread and self._step_experiment_thread.is_alive()):
				print("Performing graceful step experiment cleanup")

				try:
					# Signal graceful shutdown
					self._cleanup_event.set()

					# Try to end experiment gracefully first
					if self._step_experiment_active:
						try:
							self.framework.end_experiment()
							time.sleep(2)  # Give it time to process
						except Exception as e:
							print(f"Error sending end command during cleanup: {e}")

					# If still active, force cleanup
					if self._step_experiment_active or (self._step_experiment_thread and self._step_experiment_thread.is_alive()):
						self._force_cleanup_experiment()

					print("Graceful cleanup completed")

				except Exception as e:
					print(f"Error during graceful cleanup, forcing: {e}")
					self._force_cleanup_experiment()
			else:
				print("No active step experiment to cleanup")

	@classmethod
	def _global_cleanup(cls):
		"""Global cleanup for all active step threads."""
		print("Performing global step experiment cleanup")

		active_threads = list(cls._active_step_threads)
		if active_threads:
			print(f"Found {len(active_threads)} active step threads to cleanup")

			for thread in active_threads:
				if thread.is_alive():
					print(f"Waiting for thread to finish: {thread.name}")
					thread.join(timeout=5)

					if thread.is_alive():
						print(f"Warning: Thread did not finish: {thread.name}")

		print("Global cleanup completed")

	# ==================== NORMAL MODEMETHODS (Enhanced) ====================

	def execute_experiment(self, experiment_data: Dict, s2t_config: Dict = None, extmask: Dict = None,
						  experiment_name: str = None) -> List[str]:
		"""Execute experiment through API"""
		try:
			return self.framework.RecipeExecutor(
				data=experiment_data,
				S2T_BOOT_CONFIG=s2t_config,
				experiment_name=experiment_name,
				extmask=extmask
			)
		except Exception as e:
			print(f"API execution error: {e}")
			return ["FAILED"]

	def halt_execution(self) -> Dict:
		"""Halt current execution"""
		success = self.framework.halt_execution()
		return {
			'success': success,
			'message': 'Halt command sent' if success else 'No execution to halt',
			'state': self.framework.get_execution_state()
		}

	def continue_execution(self) -> Dict:
		"""Continue halted execution"""
		success = self.framework.continue_execution()
		return {
			'success': success,
			'message': 'Continue command sent' if success else 'No halted execution to continue',
			'state': self.framework.get_execution_state()
		}

	# Old method is replaced by end_current_execution
	def end_experiment(self) -> Dict:
		"""End current experiment gracefully (works in both modes)"""
		success = self.framework.end_experiment()
		return {
			'success': success,
			'message': 'End command sent - experiment will finish current iteration and stop' if success else 'No experiment running or failed to send end command',
			'state': self.framework.get_execution_state()
		}

	# ==================== COMMAND ACKNOWLEDGMENT METHODS ====================

	def wait_for_command_acknowledgment(self, command: ExecutionCommand, command_name: str = None,
									  max_wait_time: float = 15.0) -> Dict:
		"""
		Wait for command acknowledgment using persistent state.
		Public method for all API consumers to use.

		Args:
			command: The command to wait for
			command_name: Human readable command name for logging (optional)
			max_wait_time: Maximum time to wait in seconds

		Returns:
			Dict with acknowledgment status and details
		"""
		if not command_name:
			command_name = command.name.lower().replace('_', ' ')

		debug_log(f"API: Waiting for {command_name} acknowledgment (timeout: {max_wait_time}s)", 1, "API_WAIT_ACK")

		start_time = time.time()
		check_interval = 1  # Check every 100ms

		print(f"API: Waiting for {command_name} command acknowledgment via persistent state...")

		# First, give the command a moment to be processed
		time.sleep(0.2)

		while time.time() - start_time < max_wait_time:
			# Check for persistent success state
			persistent_state = self.framework.execution_state.get_persistent_command_state(command)

			if persistent_state['found'] and persistent_state.get('state') == 'success':
				wait_time = time.time() - start_time
				debug_log(f"Command {command_name} acknowledged in {wait_time:.2f}s", 1, "ACK_SUCCESS")
				print(f"API: {command_name} command acknowledged in {wait_time:.2f}s")

				# Clear the persistent state after successful read
				self.framework.execution_state.clear_persistent_command_state(command)

				return {
					'acknowledged': True,
					'wait_time': wait_time,
					'command': command.name,
					'persistent_data': persistent_state.get('data', {}),
					'thread_info': {
						'thread_id': persistent_state.get('thread_id'),
						'thread_name': persistent_state.get('thread_name')
					}
				}

			# Check if command is still active (being processed)
			command_active = self.framework.execution_state.has_command(command)

			if not command_active and not persistent_state['found']:
				# Command is gone and no persistent state - might have been processed differently
				wait_time = time.time() - start_time
				debug_log(f"Command {command_name} no longer active after {wait_time:.2f}s (no persistent state)", 1, "ACK_QUICK")
				print(f"API: {command_name} command no longer active after {wait_time:.2f}s (no persistent state found)")

				# For step continue, this might be normal if framework processed it quickly
				if command == ExecutionCommand.STEP_CONTINUE:
					debug_log("Assuming step continue success due to quick processing", 1, "STEP_QUICK_SUCCESS")
					return {
						'acknowledged': True,  # Assume success for step continue
						'wait_time': wait_time,
						'command': command.name,
						'reason': 'command_processed_quickly',
						'note': 'Command no longer active, assuming successful processing'
					}

			time.sleep(check_interval)

		# Timeout reached - check final state
		final_state = self.framework.execution_state.get_persistent_command_state(command)
		command_still_active = self.framework.execution_state.has_command(command)

		debug_log(f"Command {command_name} acknowledgment timed out after {max_wait_time}s", 2, "ACK_TIMEOUT")
		print(f"API: {command_name} command acknowledgment timed out after {max_wait_time}s")
		print(f"API: Final state - Command active: {command_still_active}, Persistent state found: {final_state['found']}")

		return {
			'acknowledged': False,
			'reason': 'timeout',
			'wait_time': max_wait_time,
			'command': command.name,
			'final_persistent_state': final_state,
			'command_still_active': command_still_active,
			'max_wait_time': max_wait_time
		}

	def issue_and_wait_for_acknowledgment(self, command_func, command: ExecutionCommand,
										command_name: str = None, max_wait_time: float = 15.0) -> Dict:
		"""
		Issue a command and wait for its acknowledgment in one call.
		Convenience method that combines command issuing with acknowledgment waiting.

		Args:
			command_func: Function to call to issue the command
			command: The ExecutionCommand enum value
			command_name: Human readable name for logging
			max_wait_time: Maximum time to wait for acknowledgment

		Returns:
			Dict with combined results
		"""
		if not command_name:
			command_name = command.name.lower().replace('_', ' ')

		# Clear any previous persistent state first
		self.framework.execution_state.clear_persistent_command_state(command)

		# Issue the command
		try:
			issue_result = command_func()
			print(f"API: {command_name} command issued")
		except Exception as e:
			return {
				'success': False,
				'acknowledged': False,
				'error': f'Exception while issuing {command_name} command: {str(e)}',
				'command': command.name
			}

		# Wait for acknowledgment
		ack_result = self.wait_for_command_acknowledgment(command, command_name, max_wait_time)

		# Combine results
		return {
			'success': True,
			'command_issued': True,
			'acknowledged': ack_result['acknowledged'],
			'command': command.name,
			'issue_result': issue_result,
			'acknowledgment_result': ack_result,
			'wait_time': ack_result.get('wait_time', 0),
			'reason': ack_result.get('reason') if not ack_result['acknowledged'] else None
		}

	# ==================== ENHANCED COMMAND METHODS WITH ACKNOWLEDGMENT ====================

	def continue_next_iteration_with_ack(self, max_wait_time: float = 15.0) -> Dict:
		"""Continue to next iteration and wait for acknowledgment"""
		debug_log(f"API: Issuing step continue with acknowledgment (timeout: {max_wait_time}s)", 1, "API_STEP_CONTINUE")

		result = self.issue_and_wait_for_acknowledgment(
			command_func=self.framework.step_continue,
			command=ExecutionCommand.STEP_CONTINUE,
			command_name="step continue",
			max_wait_time=max_wait_time
		)

		debug_log(f"Step continue with ack result: {result['acknowledged']}", 1, "API_STEP_RESULT")
		return result

	def end_current_experiment_with_ack(self, max_wait_time: float = 15.0) -> Dict:
		"""End current experiment and wait for acknowledgment"""
		debug_log(f"API: Issuing end experiment with acknowledgment (timeout: {max_wait_time}s)", 1, "API_END_EXPERIMENT")

		result =  self.issue_and_wait_for_acknowledgment(
			command_func=self.framework.end_experiment,
			command=ExecutionCommand.END_EXPERIMENT,
			command_name="end experiment",
			max_wait_time=max_wait_time
		)

		debug_log(f"End experiment with ack result: {result['acknowledged']}", 1, "API_END_RESULT")
		return result

	def cancel_experiment_with_ack(self, max_wait_time: float = 10.0) -> Dict:
		"""Cancel experiment and wait for acknowledgment"""
		debug_log(f"API: Issuing cancel experiment with acknowledgment (timeout: {max_wait_time}s)", 1, "API_CANCEL_EXPERIMENT")

		result = self.issue_and_wait_for_acknowledgment(
			command_func=self.framework.cancel_execution,
			command=ExecutionCommand.CANCEL,
			command_name="cancel",
			max_wait_time=max_wait_time
		)

		debug_log(f"Cancel experiment with ack result: {result['acknowledged']}", 1, "API_CANCEL_RESULT")
		return result

	def pause_execution_with_ack(self, max_wait_time: float = 10.0) -> Dict:
		"""Pause execution and wait for acknowledgment"""
		debug_log(f"API: Issuing pause/hold experiment with acknowledgment (timeout: {max_wait_time}s)", 1, "API_PAUSE_EXPERIMENT")

		result = self.issue_and_wait_for_acknowledgment(
			command_func=self.framework.halt_execution,
			command=ExecutionCommand.PAUSE,
			command_name="pause",
			max_wait_time=max_wait_time
		)

		debug_log(f"Pause / Hold experiment with ack result: {result['acknowledged']}", 1, "API_PAUSE_RESULT")
		return result

	def resume_execution_with_ack(self, max_wait_time: float = 10.0) -> Dict:
		"""Resume execution and wait for acknowledgment"""
		debug_log(f"API: Issuing continue experiment with acknowledgment (timeout: {max_wait_time}s)", 1, "API_CONTINUE_EXPERIMENT")

		result = self.issue_and_wait_for_acknowledgment(
			command_func=self.framework.continue_execution,
			command=ExecutionCommand.RESUME,
			command_name="resume",
			max_wait_time=max_wait_time
		)

		debug_log(f"Continue experiment with ack result: {result['acknowledged']}", 1, "API_CONTINUE_RESULT")
		return result

	# ==================== BACKWARD COMPATIBILITY METHODS ====================

	def continue_next_iteration(self) -> Dict:
		"""Continue to next iteration - backward compatibility method"""
		success = self.framework.step_continue()

		return {
			'success': True,  # Always return True, let caller check acknowledgment separately
			'message': 'Continue command issued - use wait_for_command_acknowledgment() for confirmation',
			'state': self.framework.get_execution_state(),
			'initial_command_result': success,
			'note': 'Use continue_next_iteration_with_ack() for automatic acknowledgment waiting'
		}

	def end_current_experiment(self) -> Dict:
		"""End current experiment - backward compatibility method"""
		success = self.framework.end_experiment()

		return {
			'success': True,  # Always return True, let caller check acknowledgment separately
			'message': 'End command issued - use wait_for_command_acknowledgment() for confirmation',
			'state': self.framework.get_execution_state(),
			'initial_command_result': success,
			'note': 'Use end_current_experiment_with_ack() for automatic acknowledgment waiting'
		}

	def cancel_experiment(self) -> Dict:
		"""Cancel experiment immediately"""
		self.framework.cancel_execution()
		return {
			'success': True,
			'message': 'Cancel command sent - experiment will stop immediately',
			'state': self.framework.get_execution_state()
		}

	# ==================== OTHER METHODS ====================

	def get_current_state(self) -> Dict:
		"""Get current execution state"""
		return self.framework.get_execution_state()

	def get_iteration_statistics(self) -> Dict:
		"""Get detailed statistics for decision making"""
		try:
			# Get statistics from the status handler instead of framework
			if (hasattr(self.framework, 'status_manager') and
				hasattr(self.framework.status_manager, 'status_reporter') and
				hasattr(self.framework.status_manager.status_reporter, 'state_machine')):

				state_machine = self.framework.status_manager.status_reporter.state_machine
				return state_machine.get_current_statistics()

			# Fallback to empty statistics
			return {
				'total_completed': 0,
				'pass_rate': 0.0,
				'fail_rate': 0.0,
				'recent_trend': 'insufficient_data',
				'recommendation': 'continue',
				'end_requested': False,
				'sufficient_data': False,
				'error': 'Status handler not available'
			}

		except Exception as e:
			print(f"Error getting iteration statistics: {e}")
			return {
				'total_completed': 0,
				'pass_rate': 0.0,
				'fail_rate': 0.0,
				'recent_trend': 'error',
				'recommendation': 'continue',
				'end_requested': False,
				'sufficient_data': False,
				'error': str(e)
			}

	def _set_upload_to_db(self, value):
		'''Method to set the Upload to Databas option'''
		if self.framework:
			self.framework.upload_to_database = value

	def force_experiment_stop(self) -> Dict:
		"""Force stop the experiment immediately"""
		try:
			# First try normal cancel
			cancel_result = self.cancel_experiment()

			# If framework has emergency stop capability, use it
			if hasattr(self.framework.execution_state, 'emergency_stop'):
				self.framework.execution_state.emergency_stop()

			# Also cleanup step experiment if active
			if self._step_experiment_active:
				self._force_cleanup_experiment()

			return {
				'success': True,
				'message': 'Experiment force stopped',
				'cancel_result': cancel_result
			}
		except Exception as e:
			return {
				'success': False,
				'error': f'Failed to force stop experiment: {str(e)}'
			}

	# This was deprecated -- Check
	def validate_step_mode_ready(self) -> Dict:
		"""Validate that the framework is ready for step-by-step operation"""
		state = self.framework.get_execution_state()

		validation_results = {
			'step_mode_enabled': state.get('step_mode_enabled', False),
			'is_running': state.get('is_running', False),
			'waiting_for_command': state.get('waiting_for_command', False),
			'can_continue': False,
			'can_end': False,
			'issues': []
		}

		# Check if we can continue
		if (validation_results['step_mode_enabled'] and
			validation_results['is_running'] and
			validation_results['waiting_for_command']):
			validation_results['can_continue'] = True

		# Check if we can end
		if validation_results['is_running']:
			validation_results['can_end'] = True

		# Identify issues
		if not validation_results['step_mode_enabled']:
			validation_results['issues'].append('Step mode not enabled')

		if not validation_results['is_running']:
			validation_results['issues'].append('No experiment running')

		return validation_results

	def _update_unit_data(self):
		'''Method to set the Check Unit Data option'''
		if self.framework:
			self.framework.update_unit_data()

	def __del__(self):
		"""Destructor to ensure cleanup."""
		try:
			self.cleanup_step_experiment()
		except Exception as e:
			print(f"Error in destructor cleanup: {e}")

	# ==================== DEBUG LOGGING ====================

	def _enable_debug_logging(self, file=None):
		enable_debug_logging(file, True)

	def _disable_debug_logging(self):
		disable_debug_logging()

class FrameworkInstanceManager:
	"""Manages Framework instances without Tkinter dependencies"""

	def __init__(self, framework_class):
		self.framework_class = framework_class
		self._current_framework = None
		self._current_api = None
		self._execution_lock = threading.Lock()

	def create_framework_instance(self, status_reporter, execution_state):
		"""Create new Framework instance for execution"""
		with self._execution_lock:
			if self._current_framework:

				self.cleanup_current_instance()

			# Create fresh Framework instance
			self._current_framework = self.framework_class(
				status_reporter=status_reporter
			)

			self._current_framework.set_execution_state(execution_state)
			self._current_framework.set_status_manager(status_reporter)

			# Create API wrapper
			self._current_api = FrameworkExternalAPI(self._current_framework)

			return self._current_api

	def get_current_api(self):
		"""Get current API instance"""
		return self._current_api

	def cleanup_current_instance(self, msg = "cleanup"):
		"""Clean up current Framework instance"""
		with self._execution_lock:

			if self._current_framework:
				try:
					self._current_framework._finalize_execution(msg)
				except Exception as e:
					print(f"Framework cleanup error: {e}")
				finally:
					self._current_framework = None
					self._current_api = None

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

	data_from_sheets = FrameworkUtils.Recipes(path)

	return data_from_sheets

def RecipeLoader(data, extmask = None, summary = True, skip = [], upload_to_database=True):

	Framework.RecipeLoader(data, extmask, summary, skip, upload_to_database)

#######################################################
########## 		User Interface Calls
#######################################################

def ControlPanel():
	fcp.run(Framework, FrameworkUtils, FrameworkInstanceManager)

def AutomationPanel():
	acp.run(Framework, FrameworkUtils, FrameworkInstanceManager)

def TTLMacroTest():
	FrameworkUtils.Test_Macros_UI()

#######################################################
########## 		Masking Script
#######################################################

# Legacy Method -- Call using Framework Utils
def DebugMask(basemask=None, root=None, callback = None):
	return fut.DebugMask(basemask, root, callback)

def currentTime():
	# Define the GMT-6 timezone
	gmt_minus_6 = pytz.timezone('Etc/GMT+6')

	# Get the current time in GMT-6
	current_time_gmt_minus_6 = datetime.now(gmt_minus_6)

	# Print the current time in GMT-6
	print("Current time in GMT-6:", current_time_gmt_minus_6.strftime('%Y-%m-%d %H:%M:%S'))

	return current_time_gmt_minus_6

#######################################################
########## 		Code Debug Logging
#######################################################

def enable_debug_logging(log_file: str = None, console_output: bool = True):
	"""Enable global debug logging for the framework"""
	# First enable the global logger
	set_global_debug_enabled(True, log_file)

	# Log the enablement (this will now work since we just enabled it)
	debug_log("Framework debug logging enabled", 1, "DEBUG_CONTROL")

	if log_file:
		debug_log(f"Debug log file set to: {log_file}", 1, "DEBUG_CONTROL")

	FrameworkUtils.FrameworkPrint(f"Debug logging enabled - File: {log_file or 'Console only'}, Console: {console_output}", 1)
	debug_log("Framework debug logging enabled successfully", 1, "DEBUG_CONTROL")

def disable_debug_logging():
	"""Disable global debug logging for the framework"""
	debug_log("Disabling framework debug logging", 1, "DEBUG_CONTROL")


	FrameworkUtils.FrameworkPrint("Debug logging disabled", 1)

	# Disable the global logger last (so the above debug_log still works)
	set_global_debug_enabled(False)

def set_debug_log_file(log_file: str):
	"""Set debug log file path"""
	if not is_debug_enabled():
		FrameworkUtils.FrameworkPrint("Debug logging is disabled. Enable it first with enable_debug_logging()", 2)
		return

	debug_log(f"Changing debug log file to: {log_file}", 1, "DEBUG_CONTROL")
	set_global_debug_file(log_file)
	FrameworkUtils.FrameworkPrint(f"Debug log file set to: {log_file}", 1)

def get_debug_status() -> Dict[str, Any]:
	"""Get current debug logging status"""
	return {
		'enabled': _global_debug_logger.enabled,
		'log_file': _global_debug_logger.output_file,
		'console_output': _global_debug_logger.console_output,
		'logger_name': _global_debug_logger.name
	}

def is_debug_logging_enabled() -> bool:
	"""Check if debug logging is currently enabled"""
	return is_debug_enabled()

Hardcode_debug = False
Debug_file = r'C:\Temp\debuglogs.log' # Set for debug purposes

if Hardcode_debug:
	enable_debug_logging(Debug_file, True)

#######################################################
########## 		Initialization
#######################################################

initscript()



