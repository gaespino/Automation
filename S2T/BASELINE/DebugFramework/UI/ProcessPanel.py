import asyncio.events
import tkinter as tk
from tkinter import filedialog, messagebox,ttk
import sys
import os
import pandas as pd
import time
import threading
import queue
import multiprocessing
from contextlib import contextmanager
from colorama import Fore, Style, Back
from datetime import datetime
import socket
import json
import weakref
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
import importlib

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(parent_dir)
sys.path.append(parent_dir)

import FileHandler as fh
import MaskEditor as gme
import UI.StatusHandler as fs
from Interfaces.IFramework import IStatusReporter
#from ExecutionHandler.utils.ThreadsHandler import execution_state, ExecutionCommand
import ExecutionHandler.utils.ThreadsHandler as th

from UI.ProcessHandler.ProcessTypes import ProcessMessage, ProcessMessageType
from UI.ProcessHandler.ProcessManager import ProcessCommunicationManager


importlib.reload(th)

ExecutionCommand = th.ExecutionCommand
execution_state = th.execution_state

#importlib.reload(fh)
#importlib.reload(gme)
importlib.reload(fs)

#from .. import FileHandler as fh
#from .. import MaskEditor  as gme

# Default configuration dictionary
S2T_CONFIGURATION = {
	'AFTER_MRC_POST': 0xbf000000,
	'EFI_POST': 0xef0000ff,
	'LINUX_POST': 0x58000000,
	'BOOTSCRIPT_RETRY_TIMES': 3,
	'BOOTSCRIPT_RETRY_DELAY': 60,
	'MRC_POSTCODE_WT': 30,
	'EFI_POSTCODE_WT': 60,
	'MRC_POSTCODE_CHECK_COUNT': 5,
	'EFI_POSTCODE_CHECK_COUNT': 10,
	'BOOT_STOP_POSTCODE' : 0x0,
	'BOOT_POSTCODE_WT' : 30,
	'BOOT_POSTCODE_CHECK_COUNT' : 1
}

# Default configuration dictionary
PLATFORM_CONFIGURATION = {
	'COM_PORT': 8,
	'IP_ADDRESS': '192.168.0.2',
}

# Mapping of labels to configuration keys
CONFIG_LABELS = {
	'Bootscript retries': 'BOOTSCRIPT_RETRY_TIMES',
	'Bootscript retry PC delay': 'BOOTSCRIPT_RETRY_DELAY',
	'EFI Postcode': 'EFI_POST',
	'EFI Postcode Waittime': 'EFI_POSTCODE_WT',
	'EFI Postcode checks count': 'EFI_POSTCODE_CHECK_COUNT',
	'OTHER Postcode': 'LINUX_POST',
	'MRC Postcode': 'AFTER_MRC_POST',
	'MRC Postcode Waittime': 'MRC_POSTCODE_WT',
	'MRC Postcode checks count': 'MRC_POSTCODE_CHECK_COUNT',
	'Boot Break Postcode': 'BOOT_STOP_POSTCODE',
	'Boot Break Waittimet': 'BOOT_POSTCODE_WT',
	'Boot Break checks count': 'BOOT_POSTCODE_CHECK_COUNT'
}

# Select Execution Type Process or Threads ---
use_process = False
debug = False

#########################################################
######		Configuration Classes
#########################################################

@dataclass
class UICommand:
	command_type: str
	data: Dict[str, Any]

class UICommandType(Enum):
	START_EXPERIMENT = "start_experiment"
	CANCEL_EXPERIMENT = "cancel_experiment"
	END_EXPERIMENT = "end_experiment"
	HOLD_EXPERIMENT = "hold_experiment"

#########################################################
######		Control Panel Code
#########################################################

class TaskCancelledException(Exception):
	"""Execution Cancelled by User"""
	pass

class ThreadHandler(threading.Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
		super().__init__(group, target, name, args, kwargs, daemon=daemon)
		self._stop_event = threading.Event()
		self.exception_queue = queue.Queue()
		# Store references but don't access them from this thread
		self._target_func = target
		self._target_args = args
		self._target_kwargs = kwargs or {}
	
	def run(self):
		try:
			print(f"({self.name}) --> Started\n")
			if self._target_func:
				# Don't pass any Tkinter objects to the target function
				self._target_func(*self._target_args, **self._target_kwargs)
				print(f"({self.name}) --> Ended")
		except Exception as e:
			print(f'({self.name}) --> Exception:', e)
			self.exception_queue.put(e)
	
	def stop(self):
		print(f"\n({self.name}) --> Stop order received")
		self._stop_event.set()

	def get_exception(self):
		"""Retrieve any exception raised during thread execution."""
		if not self.exception_queue.empty():
			return self.exception_queue.get()
		return None

class DebugFrameworkControlPanel:

	def __init__(self, root, Framework):
		self.root = root
		self.root.title("Debug Framework Control Panel")

		# CRITICAL: Store only primitive data, no Tkinter variables in threads
		self.experiments_data = {}  # Use dict instead of Tkinter variables
		self.experiment_states = {}  # Track enabled/disabled state

		# Replace thread management with process management
		self.process_manager = ProcessCommunicationManager()
		self.process_manager.register_status_callback(self._handle_process_message)
				
		# Command queue for thread communication
		self.command_queue = queue.Queue()
		self.status_queue = queue.Queue()
		
		# Thread management
		#self.framework_thread = None
		#self.thread_active = False

		# Add process state tracking
		self.process_active = False
		self.current_process_data = {}
					
		# Set minimum window size and make it resizable
		self.root.minsize(800, 600)  # Minimum size to accommodate both panels
		#self.root.geometry("1400x800")  # Default size
		
		# Configure ttk styles for better appearance
		self.setup_styles()

		self.experiments = {}
		self.experiment_frames = []
		self.hold_active = False
		self.cancel_requested = threading.Event()
		self.exception_queue = queue.Queue()
		self.current_experiment_index = 0
		self.S2T_CONFIG = Framework.system_2_tester_default() if Framework != None else S2T_CONFIGURATION
		self.mask_dict = {}
		self.mask_dict['Default'] = None

		# Enables Cancellation Check on S2T side
		self.s2t_cancel_enabled = True

		# Framework execution state tracking
		self.framework_execution_active = False
		self.current_framework_thread = None
		self.current_experiment_data = {}
		self.upload_unit_data = False
		
		# Progress tracking variables
		self.current_experiment_name = None
		self.current_experiment_index = 0
		self.total_experiments = 0
		self.current_iteration = 0
		self.total_iterations_in_experiment = 0
		self.current_iteration_progress = 0.0

		# Initialize timing estimates
		self.avg_iterations_per_experiment = 10  # Default
		self.start_time = None
		self.last_iteration_time = None
	
		self.create_widgets()

		# Auto-size after widgets are created
		self.root.after(100, self.auto_size_window)

		# Add cleanup handling
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
		
		# Keep track of active threads
		self.active_threads = []

		# Enhanced status management
		#self._status_callback_enabled = True
		#self._original_framework_callback = None
		
		# Initialize MainThreadHandler
		self.main_thread_handler = fs.MainThreadHandler(self.root, self)
	
		# CRITICAL: Initialize Framework with queue-based reporter
		if Framework:
			self.Framework = Framework(status_reporter=self.main_thread_handler)  # No direct callback
			# Use enhanced thread-safe state
			self.execution_state = execution_state #self.Framework.execution_state
			self.Framework.execution_state = execution_state # Reassigning to this execution_state
		else:
			self.Framework = None
			self.execution_state = execution_state
		
		# Cleanup handling
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
	
	# ==================== ENHANCED COMMAND METHODS ====================

	def start_tests(self):
		"""Enhanced start_tests with proper experiment counting"""
		# Count total enabled experiments
		enabled_experiments = [frame for frame, _, enabled_var, _, _, _ in self.experiment_frames if enabled_var.get()]
		self.total_experiments = len(enabled_experiments)
		self.current_experiment_index = 0

		# Reset progress tracking
		self.reset_progress_tracking()

		self.hold_active = False
		self.hold_button.configure(text=" Hold ", style="Hold.TButton")  # Reset hold button color
		self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")
		self.update_unit_data()
		self.upload_data_to_db()

	
		for index in range(self.current_experiment_index, len(self.experiment_frames)):
			frame, run_label, enabled_var, data, mask_var, experiment_name = self.experiment_frames[index]
			success = False

			fail_on_loop = 2
			if index == fail_on_loop:
				sim_fail = True
			else: sim_fail = False
			
			# Check for Cancellation
			if self.cancel_requested.is_set():
				run_label.configure(text="Cancelled", bg="gray", fg="black")
				self.log_status(f"Experiment '{experiment_name}' cancelled")
				
				# UPDATE UI HERE - we're in the main test thread, safer
				run_label.configure(text="Cancelled", bg="gray", fg="white")
				self.root.after(0, self._update_ui_after_cancel)
				break
				
			# Check for END Command BEFORE starting experiment
			if hasattr(self, 'end_after_current') and self.end_after_current:
				self.log_status(f"Stopping execution before '{experiment_name}' due to END command")
				
				# UPDATE UI HERE - safer location
				run_label.configure(text="Cancelled", bg="gray", fg="white")
				self.root.after(0, self._update_ui_after_end)
				break
			   
			if enabled_var.get():
				self.current_experiment_index = index
				test_mode = data.get('Test Type', '')
				self.root.after(0, lambda: run_label.configure(text="In Progress", bg="#00008B", fg="white"))
				self.log_status(f"Starting experiment '{experiment_name}' - {test_mode}")
				#self.root.update_idletasks()

				try:
					if self.Framework == None:
						
						success = execute(task_name = test_mode, target_func=TestLogic2, exceptions = self.exception_queue, cancel_flag = self.s2t_cancel_enabled, args =(test_mode, sim_fail), use_process = use_process)
					else:
						# Set framework execution state
						self.framework_execution_active = True
						
						# Pass the cancel flag to framework
						#if hasattr(self.Framework, 'cancel_flag'):
						#	self.Framework.cancel_flag = self.cancel_requested
													
						success = execute(task_name = test_mode, target_func=Framework_call, 
											exceptions = self.exception_queue, cancel_flag = self.s2t_cancel_enabled, 
											args =(self.Framework, data, self.S2T_CONFIG, experiment_name), 
											use_process = use_process)

						# Reset framework execution state
						self.framework_execution_active = False
			
				except TaskCancelledException as e:
					self.log_status(f"Experiment '{experiment_name}' cancelled by user")
					self.root.after(0, lambda: run_label.configure(text="Cancelled", bg="gray", fg="white"))
					#run_label.configure(text="Cancelled", bg="gray", fg="white")
					self.status_label.configure(text=" Ready ", bg="white", fg="black")
					self.cancel_requested.clear()
					self.framework_execution_active = False
					#sys.exit()
					break

				except InterruptedError as e:
					self.log_status(f"Experiment '{experiment_name}' interrupted")
					self.root.after(0, lambda: run_label.configure(text="Cancelled", bg="gray", fg="white"))
					self.status_label.configure(text=" Ready ", bg="white", fg="black")
					self.cancel_requested.clear()
					self.framework_execution_active = False
					#sys.exit()
					break

				except Exception as e:
					self.log_status(f"Experiment '{experiment_name}' failed: {str(e)}")
					run_label.configure(text="Fail", bg="yellow", fg="black")
					self.framework_execution_active = False
					if self.stop_on_fail_var.get():
						break

				# Check for exceptions from threads
				if check_exceptions(self.exception_queue):
					self.log_status(f"Experiment '{experiment_name}' failed due to exception")
					self.root.after(0, lambda: run_label.configure(text="Cancelled", bg="gray", fg="white"))
					self.status_label.configure(text=" Ready ", bg="white", fg="black")
					self.framework_execution_active = False
					break				

				if success:	
					self.log_status(f"Experiment '{experiment_name}' completed successfully")
					self.root.after(0, lambda: run_label.configure(text="Done", bg="#006400", fg="white"))
					#run_label.configure(text="Done", bg="#006400", fg="white")
				else:					
					self.log_status(f"Experiment '{experiment_name}' failed")
					self.root.after(0, lambda: run_label.configure(text="Fail", bg="yellow", fg="black"))
					#run_label.configure(text="Fail", bg="yellow", fg="black")
					if self.stop_on_fail_var.get():
						break
					
				# Check for END command after completion
				if self.Framework and hasattr(self.Framework, '_check_end_experiment_request'):
					if self.Framework._check_end_experiment_request():
						self.log_status(f"Stopping execution after experiment '{experiment_name}' due to END command")
						
						# UPDATE UI HERE
						self.root.after(0, lambda: run_label.configure(text="Cancelled", bg="gray", fg="white"))
						#run_label.configure(text="Cancelled", bg="gray", fg="white")
						self.root.after(0, self._update_ui_after_end)
						break
				
				# Check for non-framework END
				if hasattr(self, 'end_after_current') and self.end_after_current:
					self.log_status(f"Stopping execution after experiment '{experiment_name}' due to END command")
					self.status_label.configure(text=" Ended ", bg="orange", fg="black")
					break
				
				# Check for HOLD after completion
				if self.hold_active:
					self.current_experiment_index = index + 1
					self.status_label.configure(text=" Halted ", bg="yellow", fg="black")
					self.log_status("Test sequence halted by user")
					break
				
				self.current_experiment_index = index + 1
			else:
				self.log_status(f"Experiment '{experiment_name}' skipped (disabled)")
				self.current_experiment_index = index + 1
	
		# If all tests are completed
		if not self.hold_active and self.current_experiment_index >= len(self.experiment_frames):
			self.status_label.configure(text=" Completed ", bg="#006400", fg="white")
			self.log_status("All experiments completed")

		# Enable Run button and disable Cancel and Hold buttons
		self.run_button.configure(state=tk.NORMAL)
		self.cancel_button.configure(state=tk.DISABLED)
		self.hold_button.configure(state=tk.DISABLED, text=" Hold ", style="Hold.TButton")
		self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
		self.power_control_button.configure(state=tk.NORMAL)
		self.ipc_control_button.configure(state=tk.NORMAL)
		
		# IMPORTANT: Reset END state when tests complete
		self._reset_end_state_after_completion()

		# Final UI updates when all tests complete
		self.root.after(0, self._update_ui_after_completion)
	
	def toggle_framework_hold(self):
		"""Toggle framework halt/continue functionality using command system"""
		if self.Framework and self.execution_state.get_state('execution_active'):
			if not self.execution_state.is_paused():
				# Halt the framework
				success = self.Framework.halt_execution()
				if success:
					self.hold_button.configure(text="Continue", style="Continue.TButton")
					self.log_status("Framework halt command issued")
					self.status_label.configure(text=" Halting... ", bg="orange", fg="black")
			else:
				# Continue the framework
				success = self.Framework.continue_execution()
				if success:
					self.hold_button.configure(text="Hold", style="Hold.TButton")
					self.log_status("Framework continue command issued")
					self.status_label.configure(text=" Resuming... ", bg="#BF0000", fg="white")
		else:
			self.log_status("No active framework execution to control")
	
	def end_current_experiment(self):
		"""End current experiment gracefully using command system"""
		try:
			self.log_status("END command requested")
			
			if self.Framework and self.execution_state.get_state('execution_active'):
				success = self.Framework.end_experiment()
				if success:
					self.log_status("END command issued to framework")
					self.end_button.configure(text="Ending...", state=tk.DISABLED, style="EndActive.TButton")
				else:
					self.log_status("Failed to issue END command - no experiment running")
			else:
				self.log_status("No active framework execution to end")
				
		except Exception as e:
			self.log_status(f"Error issuing END command: {e}")
	
	def cancel_tests(self):
		"""Enhanced cancel with command system"""
		try:
			self.log_status("CANCEL command requested")
			
			if self.Framework:
				success = self.Framework.cancel_execution()
				if success:
					self.log_status("CANCEL command issued to framework")
					
					# Immediately update UI state
					self.thread_active = False
					self.cancel_button.configure(state=tk.DISABLED)
					self.end_button.configure(state=tk.DISABLED)
					
					# Schedule UI cleanup
					self.root.after(2000, self._cleanup_after_cancel)
				else:
					self.log_status("Failed to issue CANCEL command")
			else:
				self.log_status("No framework available to cancel")
				
		except Exception as e:
			self.log_status(f"Error issuing CANCEL command: {e}")
	
	def _cleanup_after_cancel(self):
		"""Cleanup after cancellation with command system"""
		try:

			# Check if cancellation was processed or force cleanup after timeout
			if (not self.execution_state.has_command(ExecutionCommand.CANCEL) or 
				not self.thread_active):
				self.log_status("Cancellation completed successfully")
				self.status_label.configure(text=" Cancelled ", bg="gray", fg="white")
				self._reset_buttons_after_cancel()
			else:
				# Still processing, check again but with limit
				if not hasattr(self, '_cancel_retry_count'):
					self._cancel_retry_count = 0
				
				self._cancel_retry_count += 1
				if self._cancel_retry_count < 10:  # Max 5 seconds (10 * 500ms)
					self.root.after(500, self._cleanup_after_cancel)
				else:
					# Force cleanup after timeout
					self.log_status("Force cleanup after cancel timeout")
					self._reset_buttons_after_cancel()
					self._cancel_retry_count = 0
				
		except Exception as e:
			self.log_status(f"Error in cancel cleanup: {e}")
	
	def _reset_buttons_after_cancel(self):
		"""Reset buttons after cancellation is complete"""
		try:
			self.thread_active = False

			self.run_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text=" Hold ")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.power_control_button.configure(state=tk.NORMAL)
			self.ipc_control_button.configure(state=tk.NORMAL)
			
			# Final status update
			self.root.after(2000, lambda: self.status_label.configure(text=" Ready ", bg="white", fg="black"))
			# Reset cancel retry
			if hasattr(self, '_cancel_retry_count'):
				self._cancel_retry_count = 0			
		except Exception as e:
			self.log_status(f"Error resetting buttons: {e}")

	# ==================== PROCESS EXECUTION WITH COMMAND SYSTEM ====================

	
	def _handle_process_message(self, message: ProcessMessage):
		"""Handle messages from Framework process (called from communication thread)"""
		# Schedule UI update in main thread
		self.root.after(0, lambda: self._process_message_in_main_thread(message))
	
	def _process_message_in_main_thread(self, message: ProcessMessage):
		"""Process message in main thread for safe UI updates"""
		try:
			if message.type == ProcessMessageType.PROCESS_READY:
				self._handle_process_ready(message.data)
				
			elif message.type == ProcessMessageType.EXPERIMENT_START:
				self._handle_experiment_start_process(message.data)
				
			elif message.type == ProcessMessageType.PROGRESS_UPDATE:
				self._handle_progress_update_process(message.data)
				
			elif message.type == ProcessMessageType.ITERATION_COMPLETE:
				self._handle_iteration_complete_process(message.data)
				
			elif message.type == ProcessMessageType.STRATEGY_PROGRESS:
				self._handle_strategy_progress_process(message.data)
				
			elif message.type == ProcessMessageType.EXPERIMENT_COMPLETE:
				self._handle_experiment_complete_process(message.data)
				
			elif message.type == ProcessMessageType.PROCESS_COMPLETE:
				self._handle_process_complete(message.data)
				
			elif message.type == ProcessMessageType.PROCESS_ERROR:
				self._handle_process_error(message.data)
				
			elif message.type == ProcessMessageType.STATUS_UPDATE:
				self._handle_generic_status_update(message.data)
				
		except Exception as e:
			print(f"Error processing message: {e}")
	
	def start_tests_process(self):
		"""Start tests using process instead of thread"""
		if self.process_active:
			self.log_status("Tests already running in process")
			return
		
		# Prepare experiment data (primitive data only)
		enabled_experiments = []
		for experiment_name, enabled in self.experiment_states.items():
			if enabled and experiment_name in self.experiments:
				exp_data = self._create_primitive_experiment_data(experiment_name)
				enabled_experiments.append(exp_data)
		
		if not enabled_experiments:
			self.log_status("No experiments enabled")
			return
		
		# Prepare configuration
		config_data = {
			"s2t_config": dict(self.S2T_CONFIG) if self.S2T_CONFIG else {},
			"options": {
				'stop_on_fail': self.stop_on_fail_var.get(),
				'check_unit_data': self.check_unit_data_var.get(),
				'upload_to_db': self.upload_unit_data_var.get()
			}
		}
		
		# Update UI for start
		self._update_ui_for_process_start()
		
		# Start Framework process
		success = self.process_manager.start_framework_process(enabled_experiments, config_data, self.Framework)
		
		if success:
			self.process_active = True
			self.log_status(f"Started Framework process for {len(enabled_experiments)} experiments")
		else:
			self.log_status("Failed to start Framework process")
			self._reset_ui_after_process_error()
	
	def cancel_tests_process(self):
		"""Cancel tests running in process"""
		if not self.process_active:
			self.log_status("No process to cancel")
			return
		
		self.log_status("Sending cancel command to Framework process...")
		success = self.process_manager.send_command_to_framework(
			ProcessMessageType.CANCEL_COMMAND,
			{"reason": "User cancellation"}
		)
		
		if success:
			self.cancel_button.configure(state=tk.DISABLED)
			self.status_label.configure(text=" Cancelling... ", bg="orange", fg="black")
		else:
			self.log_status("Failed to send cancel command")
	
	def end_current_experiment_process(self):
		"""End current experiment in process"""
		if not self.process_active:
			self.log_status("No process to end")
			return
		
		self.log_status("Sending end command to Framework process...")
		success = self.process_manager.send_command_to_framework(
			ProcessMessageType.END_COMMAND,
			{"reason": "User requested end"}
		)
		
		if success:
			self.end_button.configure(text="Ending...", state=tk.DISABLED)
		else:
			self.log_status("Failed to send end command")
	
	def toggle_framework_hold_process(self):
		"""Toggle framework halt/continue in process"""
		if not self.process_active:
			self.log_status("No process to control")
			return
		
		# Check current state and send appropriate command
		if self.hold_button.cget("text") == " Hold ":
			# Send pause command
			success = self.process_manager.send_command_to_framework(
				ProcessMessageType.PAUSE_COMMAND,
				{"reason": "User requested pause"}
			)
			if success:
				self.hold_button.configure(text="Continue", style="Continue.TButton")
				self.log_status("Pause command sent to Framework process")
		else:
			# Send resume command
			success = self.process_manager.send_command_to_framework(
				ProcessMessageType.RESUME_COMMAND,
				{"reason": "User requested resume"}
			)
			if success:
				self.hold_button.configure(text=" Hold ", style="Hold.TButton")
				self.log_status("Resume command sent to Framework process")
	
	# Process message handlers
	def _handle_process_ready(self, data):
		"""Handle process ready message"""
		self.log_status(f"Framework process ready: {data.get('message', 'Ready')}")
		experiment_count = data.get('experiment_count', 0)
		self.total_experiments = experiment_count
		self.current_experiment_index = 0
	
	def _handle_experiment_start_process(self, data):
		"""Handle experiment start from process"""
		exp_index = data.get('experiment_index', 0)
		exp_name = data.get('experiment_name', 'Unknown')
		total_exp = data.get('total_experiments', 1)
		
		self.current_experiment_index = exp_index
		self.current_experiment_name = exp_name
		
		self.log_status(f"Starting Experiment {exp_index + 1}/{total_exp}: {exp_name}")
		
		# Update experiment status in UI
		self._update_experiment_status_in_ui({
			'experiment_name': exp_name,
			'status': 'In Progress',
			'bg_color': '#00008B',
			'fg_color': 'white'
		})
	
	def _handle_progress_update_process(self, data):
		"""Handle progress update from process"""
		# Update progress display
		current_iteration = data.get('current_iteration', 0)
		total_iterations = data.get('total_iterations', 1)
		progress_weight = data.get('progress_weight', 0.0)
		status = data.get('status', 'Running')
		
		self.current_iteration = current_iteration
		self.total_iterations_in_experiment = total_iterations
		self.current_iteration_progress = progress_weight
		
		# Update UI
		self._update_overall_progress()
		self.update_progress_display(status=status)
	
	def _handle_iteration_complete_process(self, data):
		"""Handle iteration complete from process"""
		iteration = data.get('iteration', 0)
		status = data.get('status', 'Complete')
		scratchpad = data.get('scratchpad', '')
		seed = data.get('seed', '')
		
		self.log_status(f"Iteration {iteration} completed: {status}")
		if scratchpad:
			self.log_status(f"  Scratchpad: {scratchpad}")
		if seed:
			self.log_status(f"  Seed: {seed}")
		
		# Update progress
		self.update_progress_display(result_status=status)
	
	def _handle_strategy_progress_process(self, data):
		"""Handle strategy progress from process"""
		progress_percent = data.get('progress_percent', 0)
		current_iteration = data.get('current_iteration', 0)
		total_iterations = data.get('total_iterations', 1)
		
		# Update progress bar directly
		self.progress_var.set(min(100, max(0, progress_percent)))
		self.progress_percentage_label.configure(text=f"{int(progress_percent)}%")
		
		iteration_text = f"Iter {current_iteration}/{total_iterations}"
		self.progress_iteration_label.configure(text=iteration_text)
	
	def _handle_experiment_complete_process(self, data):
		"""Handle experiment complete from process"""
		exp_index = data.get('experiment_index', 0)
		exp_name = data.get('experiment_name', 'Unknown')
		results = data.get('results', [])
		success = data.get('success', False)
		
		self.log_status(f"Experiment {exp_index + 1} completed: {exp_name}")
		
		# Update experiment status in UI
		status_text = "Done" if success else "Fail"
		bg_color = "#006400" if success else "yellow"
		fg_color = "white" if success else "black"
		
		self._update_experiment_status_in_ui({
			'experiment_name': exp_name,
			'status': status_text,
			'bg_color': bg_color,
			'fg_color': fg_color
		})
	
	def _handle_process_complete(self, data):
		"""Handle process completion"""
		total_executed = data.get('total_executed', 0)
		self.log_status(f"All experiments completed! Total executed: {total_executed}")
		
		self.process_active = False
		self.status_label.configure(text=" Completed ", bg="#006400", fg="white")
		self._reset_ui_after_process_complete()
	
	def _handle_process_error(self, data):
		"""Handle process error"""
		error = data.get('error', 'Unknown error')
		self.log_status(f"Framework process error: {error}")
		
		self.process_active = False
		self.status_label.configure(text=" Error ", bg="red", fg="white")
		self._reset_ui_after_process_error()
	
	def _handle_generic_status_update(self, data):
		"""Handle generic status updates"""
		message = data.get('message', 'Status update')
		self.log_status(message)
	
	# UI update methods for process
	def _update_ui_for_process_start(self):
		"""Update UI for process start"""
		self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")
		self.run_button.configure(state=tk.DISABLED)
		self.cancel_button.configure(state=tk.NORMAL)
		self.hold_button.configure(state=tk.NORMAL)
		self.end_button.configure(state=tk.NORMAL)
		self.power_control_button.configure(state=tk.DISABLED)
		self.ipc_control_button.configure(state=tk.DISABLED)
		
		# Reset experiment status
		for frame_data in self.experiment_frames:
			frame_data['run_label'].configure(text="Idle", bg="white", fg="black")
	
	def _reset_ui_after_process_complete(self):
		"""Reset UI after process completion"""
		self.run_button.configure(state=tk.NORMAL)
		self.cancel_button.configure(state=tk.DISABLED)
		self.hold_button.configure(state=tk.DISABLED, text=" Hold ")
		self.end_button.configure(state=tk.DISABLED, text="End")
		self.power_control_button.configure(state=tk.NORMAL)
		self.ipc_control_button.configure(state=tk.NORMAL)
	
	def _reset_ui_after_process_error(self):
		"""Reset UI after process error"""
		self.run_button.configure(state=tk.NORMAL)
		self.cancel_button.configure(state=tk.DISABLED)
		self.hold_button.configure(state=tk.DISABLED, text=" Hold ")
		self.end_button.configure(state=tk.DISABLED, text="End")
		self.power_control_button.configure(state=tk.NORMAL)
		self.ipc_control_button.configure(state=tk.NORMAL)
	
	def _update_experiment_status_in_ui(self, status_data):
		"""Update experiment status in UI"""
		experiment_name = status_data['experiment_name']
		for frame_data in self.experiment_frames:
			if frame_data['experiment_name'] == experiment_name:
				frame_data['run_label'].configure(
					text=status_data['status'],
					bg=status_data['bg_color'],
					fg=status_data['fg_color']
				)
				break		
	# ==================== THREAD EXECUTION WITH COMMAND SYSTEM ====================
	
	def start_tests_thread(self):
		"""Start tests with proper thread isolation and command system"""
		if self.thread_active:
			self.log_status("Tests already running")
			return
		self.execution_state.clear_all_commands()

		# Prepare for new execution
		if self.Framework:
			if not self.Framework._prepare_for_new_execution():
				self.log_status("Failed to prepare framework for execution")
				return
		
		# Prepare primitive data for thread
		enabled_experiments = []
		
		for experiment_name, enabled in self.experiment_states.items():
			if enabled and experiment_name in self.experiments:
				exp_data = self._create_primitive_experiment_data(experiment_name)
				enabled_experiments.append(exp_data)
		
		if not enabled_experiments:
			self.log_status("No experiments enabled")
			return

		# Set total_experiments BEFORE starting thread
		self.total_experiments = len(enabled_experiments)
		self.current_experiment_index = 0
		
		# Log the setup
		self.log_status(f"🚀 Setup: {self.total_experiments} experiments to execute")
		
		# Prepare configuration data (primitives only)
		s2t_config_copy = dict(self.S2T_CONFIG) if self.S2T_CONFIG else {}
		
		# Get option states (convert Tkinter vars to primitives)
		options = {
			'stop_on_fail': self.stop_on_fail_var.get(),
			'check_unit_data': self.check_unit_data_var.get(),
			'upload_to_db': self.upload_unit_data_var.get()
		}
		
		# Clear any previous thread state
		self.thread_active = True
		
		# Update UI for start
		self._update_ui_for_start()
		
		# Start thread with primitive data only
		self.framework_thread = threading.Thread(
			target=self._run_experiments_thread,
			args=(enabled_experiments, s2t_config_copy, options),
			daemon=True,
			name="FrameworkExecution"
		)
		self.framework_thread.start()
		
		self.log_status(f"Started execution thread for {len(enabled_experiments)} experiments")

	def _run_experiments_thread(self, experiments_list, s2t_config, options):
		"""Enhanced thread execution with command system"""
		try:
			total_experiments = len(experiments_list)

			# Initialize execution state
			self.execution_state.update_state(
				execution_active=True,
				current_experiment=None,
				current_iteration=0,
				total_iterations=0
			)
			
			# Send setup notification
			self.main_thread_handler.queue_status_update({
				'type': 'execution_setup',
				'data': {
					'total_experiments': total_experiments,
					'experiment_names': [exp['experiment_name'] for exp in experiments_list]
				}
			})			
			
			# Update framework options
			if self.Framework:
				self.Framework.upload_to_database = options['upload_to_db']
			
			for index, exp_data in enumerate(experiments_list):

				# Check for END command BEFORE starting each experiment
				if self.execution_state.is_ended():
					self.log_status(f"🛑 END command received - stopping before experiment {index + 1}")
					self._send_end_status(exp_data, index, len(experiments_list))
					break

				# Check for cancellation BEFORE starting each experiment
				if self.execution_state.should_stop() or self.execution_state.is_cancelled():
					self.log_status(f"🚫 Execution stopped before experiment {index + 1}")
					self._send_cancellation_status(exp_data, index, len(experiments_list))
					break  # CRITICAL: Break immediately
				
				experiment_name = exp_data['experiment_name']

				# Update experiment state
				self.execution_state.update_state(
					current_experiment=experiment_name,
					current_iteration=0
				)
				
				# Update UI
				self.main_thread_handler.queue_status_update({
					'type': 'experiment_index_update',
					'data': {
						'current_experiment_index': index,
						'total_experiments': total_experiments,
						'experiment_name': experiment_name
					}
				})		

				time.sleep(0.1)  # Ensure state update is processed
				
				self.main_thread_handler.queue_status_update({
					'type': 'experiment_status_update',
					'data': {
						'experiment_name': experiment_name,
						'status': 'In Progress',
						'bg_color': '#00008B',
						'fg_color': 'white'
					}
				})
				
				success = False
				
				try:
					if self.Framework is None:
						success = self._simulate_test_execution(exp_data)
					else:
						success = self._execute_framework_test(exp_data, s2t_config, experiment_name)

					# Check for END command after each experiment
					if self.execution_state.is_ended():
						self.log_status(f"🛑 END command received after experiment '{experiment_name}' - stopping execution")
						self._send_end_status(exp_data, index + 1, len(experiments_list))
						
						# Update this experiment's status to show it completed
						status_text = "Done" if success else "Fail"
						bg_color = "#006400" if success else "yellow"
						fg_color = "white" if success else "black"
						
						self.main_thread_handler.queue_status_update({
							'type': 'experiment_status_update',
							'data': {
								'experiment_name': experiment_name,
								'status': status_text,
								'bg_color': bg_color,
								'fg_color': fg_color
							}
						})
						break

					# CRITICAL: Check for cancellation after each experiment
					if self.execution_state.is_cancelled():
						self.log_status(f"Execution cancelled after experiment '{experiment_name}'")
						if self.execution_state.is_cancelled():
							self._send_cancellation_status(exp_data, index, len(experiments_list))
						break

					# CRITICAL: Check for cancellation after each experiment
					if self.execution_state.is_ended():
						self.log_status(f"Execution cancelled after experiment '{experiment_name}'")
						if self.execution_state.is_ended():
							self._send_end_status(exp_data, index, len(experiments_list))
						break

				except InterruptedError:
					self.log_status(f"Experiment '{experiment_name}' was cancelled")
					success = False
					self._send_cancellation_status(exp_data, index + 1, len(experiments_list))
					break
				except Exception as e:
					self.log_status(f"Experiment '{experiment_name}' failed: {str(e)}")
					success = False
					
					# Check for commands after exception
					if self.execution_state.is_ended():
						self._send_end_status(exp_data, index + 1, len(experiments_list))
						break
					# Send cancellation status and break immediately
					if self.execution_state.is_cancelled():
						self._send_cancellation_status(exp_data, index + 1, len(experiments_list))
						break
					
				# Check for stop after experiment
				#if self.execution_state.should_stop():
				#	self.log_status(f"Execution stopped after experiment '{experiment_name}'")
				#	if self.execution_state.is_cancelled():
				#		self._send_cancellation_status(exp_data, index + 1, len(experiments_list))
				#	break


				# If Framework returned cancelled status, stop immediately
				#if not success and self.execution_state.is_cancelled():
				#	self.log_status(f"Framework execution cancelled during '{experiment_name}'")
				#	self._send_cancellation_status(exp_data, index + 1, len(experiments_list))
				#	break

				# ✅ CRITICAL: Check for cancellation IMMEDIATELY after experiment execution
				if self.execution_state.is_cancelled():
					self.log_status(f"🚫 Execution cancelled after experiment '{experiment_name}'")
					
					# Update this experiment's status to cancelled
					self.main_thread_handler.queue_status_update({
						'type': 'experiment_status_update',
						'data': {
							'experiment_name': experiment_name,
							'status': 'Cancelled',
							'bg_color': 'gray',
							'fg_color': 'white'
						}
					})
					
					self._send_cancellation_status(exp_data, index + 1, len(experiments_list))
					break  # ✅ CRITICAL: Break immediately

				# Update experiment status
				status_text = "Done" if success else "Fail"
				bg_color = "#006400" if success else "yellow"
				fg_color = "white" if success else "black"
				
				self.main_thread_handler.queue_status_update({
					'type': 'experiment_status_update',
					'data': {
						'experiment_name': experiment_name,
						'status': status_text,
						'bg_color': bg_color,
						'fg_color': fg_color
					}
				})

				# Break if cancelled
				if self.execution_state.is_cancelled():
					break

				# Break if ended
				if self.execution_state.is_ended():
					break

				if not success and options['stop_on_fail']:
					break
				
				if index < len(experiments_list) - 1:
					time.sleep(2)
			
		except Exception as e:
			self.log_status(f"Thread execution error: {e}")

			# Send appropriate status on exception
			if self.execution_state.is_ended():
				self.main_thread_handler.queue_status_update({
					'type': 'execution_ended',
					'data': {
						'reason': f'Execution ended during error: {str(e)}',
						'error': str(e)
					}
				})
							
			# Send cancellation status on exception if cancelled
			if self.execution_state.is_cancelled():
				self.main_thread_handler.queue_status_update({
					'type': 'execution_cancelled',
					'data': {
						'reason': f'Execution error during cancellation: {str(e)}',
						'error': str(e)
					}
				})
		finally:
			# Proper cleanup using command system
			try:
				self.thread_active = False
				
				# Finalize framework execution
				if self.Framework:
					self.Framework._finalize_execution("all_experiments_complete")
				
				# Clear primitive data
				experiments_list.clear()
				s2t_config.clear()
				options.clear()
				
				# Queue completion
				if self.execution_state.is_ended():
					self.main_thread_handler.queue_status_update({
						'type': 'execution_ended_complete',
						'data': {'total_executed': len(experiments_list) if experiments_list else 0}
					})				
				# Queue completion
				else:
					self.main_thread_handler.queue_status_update({
					'type': 'all_experiments_complete',
					'data': {'total_executed': len(experiments_list) if experiments_list else 0}
					})

			except Exception as cleanup_error:
				self.log_status(f"❌ Thread cleanup error: {cleanup_error}")

	def _execute_framework_test(self, exp_data, s2t_config, experiment_name):
		"""Execute framework test with proper error handling"""
		try:

			# Check global execution state before starting
			if execution_state.is_cancelled():
				self.log_status(f"🚫 Execution already cancelled before starting '{experiment_name}'")
				return False

			if execution_state.is_ended():
				self.log_status(f"🚫 Execution already ended before starting '{experiment_name}'")
				return False
						
			# Debug Logs
			self.log_status(f"🔍 DEBUG: Starting Framework execution for '{experiment_name}'")
			self.log_status(f"🔍 DEBUG: Control Panel cancellation state: {self.execution_state.is_cancelled()}")
			self.log_status(f"🔍 DEBUG: Control Panel END state: {self.execution_state.is_ended()}")
			# Set up progress tracking
			estimated_iterations = self._estimate_experiment_iterations(exp_data)
			self.total_iterations_in_experiment = estimated_iterations
			self.current_iteration = 1
			self.current_iteration_progress = 0.0
			
			# Update experiment name for progress tracking
			self.current_experiment_name = experiment_name
		
			# Call framework with primitive data only
			result = self.Framework.RecipeExecutor(
				data=exp_data,
				S2T_BOOT_CONFIG=s2t_config,
				extmask=exp_data.get('External Mask'),
				summary=True,
				cancel_flag=None,  # Use command system instead
				experiment_name=experiment_name
			)

			self.log_status(f"🔍 DEBUG: Framework execution completed for '{experiment_name}'")
			self.log_status(f"🔍 DEBUG: Control Panel cancellation state after: {self.execution_state.is_cancelled()}")
			self.log_status(f"🔍 DEBUG: Framework result: {result}")

			# Check global execution state after Framework execution
			if execution_state.is_cancelled():
				self.log_status(f"🚫 Execution was cancelled during Framework execution of '{experiment_name}'")
				return False		
				
			# CRITICAL: Check if Framework's execution state shows cancellation
			if hasattr(self.Framework, 'execution_state'):
				if self.Framework.execution_state.is_cancelled():
					self.log_status(f"🚫 Framework execution state shows cancellation for '{experiment_name}'")
					# Propagate cancellation to Control Panel's execution state
					self.execution_state.cancel(reason="Framework execution cancelled")
					return False

			# Check if execution was cancelled through results
			if isinstance(result, list):
				failure_statuses = ['FAILED', 'CANCELLED', 'ExecutionFAIL']
				has_cancelled = any(status == 'CANCELLED' for status in result)
				
				if has_cancelled:
					self.log_status(f"🚫 Framework execution cancelled for '{experiment_name}' (detected in results)")
					# Propagate cancellation to Control Panel's execution state
					self.execution_state.cancel(reason="Framework execution returned CANCELLED status")
					return False
				
				return not any(status in failure_statuses for status in result)
						
			# Check if execution was successful
			#if isinstance(result, list):
			#	failure_statuses = ['FAILED', 'CANCELLED', 'ExecutionFAIL']
			#	return not any(status in failure_statuses for status in result)
			
			return True
			
		except InterruptedError:
			self.log_status(f"Experiment '{experiment_name}' was cancelled")
			# Propagate cancellation to Control Panel's execution state
			self.execution_state.cancel(reason="Framework execution interrupted")
			return False
		except Exception as e:
			self.log_status(f"Framework execution error for '{experiment_name}': {str(e)}")
			return False

	def _send_cancellation_status(self, exp_data, completed_count, total_count):
		"""Helper method to send cancellation status"""
		self.main_thread_handler.queue_status_update({
			'type': 'execution_cancelled',
			'data': {
				'experiment_name': exp_data.get('experiment_name', 'Unknown'),
				'completed_experiments': completed_count,
				'total_experiments': total_count,
				'reason': 'User cancellation'
			}
		})

	def _send_end_status(self, exp_data, completed_count, total_count):
		"""Helper method to send end command status"""
		self.main_thread_handler.queue_status_update({
			'type': 'execution_ended',
			'data': {
				'experiment_name': exp_data.get('experiment_name', 'Unknown'),
				'completed_experiments': completed_count,
				'total_experiments': total_count,
				'reason': 'END command - execution stopped gracefully'
			}
		})
		
	# ==================== WINDOW MANAGEMENT CODE ====================

	def on_closing(self):
		"""Enhanced cleanup for process management"""
		try:
			# Stop any running process
			if self.process_active:
				self.log_status("Terminating Framework process...")
				self.process_manager.terminate_framework_process()
			
			# Stop communication
			self.process_manager.stop_communication()
			
			# Clear queues and cleanup
			self._cleanup_tkinter_variables()
			self._cleanup_widgets()
			
		except Exception as e:
			print(f"Cleanup error: {e}")
		finally:
			try:
				self.root.quit()
				self.root.destroy()
			except:
				pass

	def _cleanup_tkinter_variables(self):
		"""Clean up Tkinter variables safely in main thread"""
		try:
			# Clear experiment frame variables
			for frame_data in getattr(self, 'experiment_frames', []):
				try:
					if isinstance(frame_data, dict):
						# New format
						if 'enabled_var' in frame_data:
							del frame_data['enabled_var']
						if 'mask_var' in frame_data:
							del frame_data['mask_var']
					else:
						# Old tuple format
						if len(frame_data) > 2:
							del frame_data[2]  # enabled_var
						if len(frame_data) > 4:
							del frame_data[4]  # mask_var
				except Exception as e:
					print(f"Error cleaning frame variables: {e}")
			
			# Clear other Tkinter variables
			vars_to_clear = [
				'stop_on_fail_var', 'check_unit_data_var', 'upload_unit_data_var',
				'auto_scroll_var', 'progress_var'
			]
			
			for var_name in vars_to_clear:
				if hasattr(self, var_name):
					try:
						delattr(self, var_name)
					except Exception as e:
						print(f"Error clearing {var_name}: {e}")
						
		except Exception as e:
			print(f"Error in Tkinter variable cleanup: {e}")
			
	# ADD helper methods
	def _clear_queue(self, q):
		"""Clear a queue safely"""
		try:
			while True:
				q.get_nowait()
		except queue.Empty:
			pass

	def _cleanup_widgets(self):
		"""Clean up widgets to prevent variable errors"""
		try:
			# Clear experiment frames
			for frame_data in getattr(self, 'experiment_frames', []):
				try:
					if 'checkbox_var' in frame_data:
						del frame_data['checkbox_var']
					if 'frame' in frame_data:
						frame_data['frame'].destroy()
				except:
					pass
			
			self.experiment_frames = []
			
		except Exception as e:
			print(f"Widget cleanup error: {e}")
			
	def cleanup_variables(self):
		"""Clean up Tkinter variables safely"""
		try:
			# Clear variable references
			if hasattr(self, 'input_vars'):
				self.input_vars.clear()
			
			# Clear other variable collections
			for frame, run_label, enabled_var, data, mask_var, experiment_name in self.experiment_frames:
				try:
					del enabled_var
					del mask_var
				except:
					pass
					
		except Exception as e:
			print(f"Error cleaning up variables: {e}")
					
	def setup_styles(self):
		"""Configure ttk styles for better appearance"""
		style = ttk.Style()
		
		# Use a darker theme - try 'alt', 'default', 'classic', or 'vista'
		# 'alt' provides a nice darker appearance
		try:
			style.theme_use('alt')  # This gives a darker, more modern look
		except:
			# Fallback to clam if alt is not available
			style.theme_use('clam')
		
		# Custom progress bar style
		style.configure("Custom.Horizontal.TProgressbar",
					troughcolor='#404040',  # Darker trough
					background='#4CAF50',  # Green progress
					lightcolor='#4CAF50',
					darkcolor='#388E3C',
					borderwidth=1,
					relief='flat')
		
		# Style for different states
		style.configure("Running.Horizontal.TProgressbar",
					background='#2196F3',  # Blue for running
					lightcolor='#2196F3',
					darkcolor='#1976D2')
		
		style.configure("Warning.Horizontal.TProgressbar",
					background='#FF9800',  # Orange for warnings
					lightcolor='#FF9800',
					darkcolor='#F57C00')
		
		style.configure("Error.Horizontal.TProgressbar",
					background='#F44336',  # Red for errors
					lightcolor='#F44336',
					darkcolor='#D32F2F')

		# Custom button styles
		style.configure("Hold.TButton", foreground="black")
		style.configure("HoldActive.TButton", foreground="orange", font=("Arial", 9, "bold"))
		style.configure("Continue.TButton", foreground="blue", font=("Arial", 9, "bold"))
		style.configure("End.TButton", foreground="red", font=("Arial", 9, "bold"))
		style.configure("EndActive.TButton", foreground="white", background="red", font=("Arial", 9, "bold"))
		
	def auto_size_window(self):
		"""Automatically size window based on content"""
		# Update all widgets to get their required sizes
		self.root.update_idletasks()
		
		# Calculate required width based on content
		left_width = max(800, self.left_frame.winfo_reqwidth())  # Minimum width for left panel
		right_width = max(400, self.right_frame.winfo_reqwidth())  # Minimum 400px for right panel
		
		# Add some padding
		total_width = left_width + right_width + 50
		
		# Calculate height based on content, but don't make it too tall
		content_height = self.root.winfo_reqheight()
		screen_height = self.root.winfo_screenheight()
		max_height = int(screen_height * 0.9)  # Max 90% of screen height
		total_height = min(max_height, max(700, content_height + 50))
		
		# Set window size
		self.root.geometry(f"{total_width}x{total_height}")
		
		# Position the sash to give right panel the space it needs
		self.root.after(50, lambda: self.main_paned.sashpos(0, total_width - right_width - 20))
		
	def create_widgets(self):
		# Create main horizontal container using ttk.PanedWindow
		self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
		self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		
		# Left side - Main UI (experiments, controls, etc.)
		self.left_frame = ttk.Frame(self.main_paned)
		self.main_paned.add(self.left_frame, weight=3)  # Gets 75% of space
		
		# Right side - Status panel
		self.right_frame = ttk.Frame(self.main_paned)
		self.main_paned.add(self.right_frame, weight=1)  # Gets 25% of space
		
		# Create left side content
		self.create_left_panel()
		
		# Create right side status panel
		self.create_right_status_panel()

	def create_left_panel(self):
		"""Create the main UI elements on the left side"""
		# Main Title
		title_frame = ttk.Frame(self.left_frame)
		title_frame.pack(fill=tk.X, padx=10, pady=5)
		
		ttk.Label(title_frame, text="Debug Framework Control Panel", font=("Arial", 16)).pack(side=tk.LEFT)

		# Status Label
		self.status_label = tk.Label(title_frame, padx=5, width=15, text=" Ready ", 
								   bg="white", fg="black", font=("Arial", 12), 
								   relief=tk.GROOVE, borderwidth=2)
		self.status_label.pack(side=tk.RIGHT)
		
		# Control buttons frame
		buttons_frame = ttk.Frame(title_frame)
		buttons_frame.pack(side=tk.RIGHT, padx=5)
		
		# Power Control Button
		self.power_control_button = ttk.Button(buttons_frame, text="Power", 
											 command=self.open_power_control_window)
		self.power_control_button.pack(side=tk.RIGHT, padx=2)

		# IPC Control Button
		self.ipc_control_button = ttk.Button(buttons_frame, text="IPC", 
										   command=self.check_ipc)
		self.ipc_control_button.pack(side=tk.RIGHT, padx=2)
		
		# Settings Button
		self.settings_button = ttk.Button(buttons_frame, text="⚙", 
										command=self.open_settings_window)
		self.settings_button.pack(side=tk.RIGHT, padx=2)

		# File selection frame
		self.file_frame = ttk.Frame(self.left_frame)
		self.file_frame.pack(fill=tk.X, padx=10, pady=5)

		ttk.Label(self.file_frame, text="Experiments:", width=12).pack(side=tk.LEFT)
		self.file_entry = ttk.Entry(self.file_frame)
		self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
		ttk.Button(self.file_frame, text="Browse", 
				  command=self.load_experiments_file).pack(side=tk.LEFT)
		
		# Separator
		ttk.Separator(self.left_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
		
		# Experiment container with scrollbar
		self.create_experiment_container()

		# Options frame
		self.create_options_frame()

		# Control buttons frame
		self.create_control_buttons()
				
	def create_options_frame(self):
		"""Create options checkboxes"""
		self.options_frame = ttk.Frame(self.left_frame)
		self.options_frame.pack(fill=tk.X, padx=10, pady=5)

		# Right side buttons
		buttons_right = ttk.Frame(self.options_frame)
		buttons_right.pack(side=tk.RIGHT)
		
		ttk.Button(buttons_right, text="Test TTL", 
				  command=self.test_ttl).pack(side=tk.RIGHT, padx=5)
		ttk.Button(buttons_right, text="Mask", 
				  command=self.open_mask_management).pack(side=tk.RIGHT, padx=5)

		# Left side checkboxes
		self.stop_on_fail_var = tk.BooleanVar(value=False)
		ttk.Checkbutton(self.options_frame, text="Stop on Fail", 
					   variable=self.stop_on_fail_var).pack(side=tk.LEFT, padx=5)

		self.check_unit_data_var = tk.BooleanVar(value=False)
		ttk.Checkbutton(self.options_frame, text="Check Unit Data", 
					   variable=self.check_unit_data_var).pack(side=tk.LEFT, padx=5)

		self.upload_unit_data_var = tk.BooleanVar(value=False)
		ttk.Checkbutton(self.options_frame, text="Upload Data (DB)", 
					   variable=self.upload_unit_data_var).pack(side=tk.LEFT, padx=5)

	def create_control_buttons(self):
		"""Create main control buttons"""
		self.control_frame = ttk.Frame(self.left_frame)
		self.control_frame.pack(fill=tk.X, padx=10, pady=10)
		
		# Left side
		self.saveas_button = ttk.Button(self.control_frame, text="Save JSON", 
									   command=self.save_config, state=tk.DISABLED)
		self.saveas_button.pack(side=tk.LEFT)
		
		# Right side
		button_frame = ttk.Frame(self.control_frame)
		button_frame.pack(side=tk.RIGHT)
		
		self.run_button = ttk.Button(button_frame, text="Run", 
								   command=self.start_tests_process)
		self.run_button.pack(side=tk.RIGHT, padx=2)
		
		self.hold_button = ttk.Button(button_frame, text="Hold", 
									command=self.toggle_framework_hold_process, 
									state=tk.DISABLED)
		self.hold_button.pack(side=tk.RIGHT, padx=2)

		self.end_button = ttk.Button(button_frame, text="End", 
								command=self.end_current_experiment_process, 
								state=tk.DISABLED)
		self.end_button.pack(side=tk.RIGHT, padx=2)
		
		self.cancel_button = ttk.Button(button_frame, text="Cancel", 
									  command=self.cancel_tests_process, 
									  state=tk.DISABLED)
		self.cancel_button.pack(side=tk.RIGHT, padx=2)

	def create_experiment_container(self):
		"""Create scrollable container for experiments"""
		# Container frame - remove white background
		container_frame = ttk.Frame(self.left_frame)
		container_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
		
		# Create canvas and scrollbar - remove highlightthickness and set proper background
		canvas = tk.Canvas(container_frame, highlightthickness=0, 
						bg=self.root.cget('bg'))  # Match root background
		v_scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
		h_scrollbar = ttk.Scrollbar(container_frame, orient="horizontal", command=canvas.xview)
		
		# Scrollable frame - use ttk.Frame for consistent theming
		self.experiment_container = ttk.Frame(canvas)
		
		# Configure scrolling
		self.experiment_container.bind(
			"<Configure>",
			lambda e: self._update_scroll_region(canvas)
		)
		
		# Bind canvas resize to update scroll region
		canvas.bind(
			"<Configure>",
			lambda e: self._update_canvas_scroll_region(canvas)
		)
		
		canvas_window = canvas.create_window((0, 0), window=self.experiment_container, anchor="nw")
		canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
		
		# Pack scrollbars and canvas
		canvas.pack(side="left", fill="both", expand=True)
		v_scrollbar.pack(side="right", fill="y")
		# Only show horizontal scrollbar if needed
		
		# Bind mousewheel to canvas
		def _on_mousewheel(event):
			canvas.yview_scroll(int(-1*(event.delta/120)), "units")
		
		def _bind_mousewheel(event):
			canvas.bind_all("<MouseWheel>", _on_mousewheel)
		
		def _unbind_mousewheel(event):
			canvas.unbind_all("<MouseWheel>")
		
		#canvas.bind('<Enter>', _bind_mousewheel)
		#canvas.bind('<Leave>', _unbind_mousewheel)
		
		# Store references for later use
		self.experiment_canvas = canvas
		self.experiment_canvas_window = canvas_window

	def _update_scroll_region(self, canvas):
		"""Update canvas scroll region"""
		canvas.configure(scrollregion=canvas.bbox("all"))

	def _update_canvas_scroll_region(self, canvas):
		"""Update canvas window width to match canvas width"""
		canvas_width = canvas.winfo_width()
		canvas.itemconfig(self.experiment_canvas_window, width=canvas_width)

	def create_right_status_panel(self):
		"""Create the right-side status panel with enhanced progress bar"""
		# Main container for right panel
		main_container = ttk.Frame(self.right_frame)
		main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
		
		# Title
		title_label = ttk.Label(main_container, text="Execution Status", 
							   font=("Arial", 12, "bold"))
		title_label.pack(pady=(0, 10))
		
		# Progress section
		progress_frame = ttk.LabelFrame(main_container, text="Current Progress", padding=10)
		progress_frame.pack(fill=tk.X, pady=(0, 10))
		
		# Strategy and test info
		self.strategy_label = ttk.Label(progress_frame, text="Strategy: Ready")
		self.strategy_label.pack(anchor="w")
		
		self.test_name_label = ttk.Label(progress_frame, text="Test: None", 
										foreground="blue")
		self.test_name_label.pack(anchor="w")
		
		# Progress info frame
		progress_info = ttk.Frame(progress_frame)
		progress_info.pack(fill=tk.X, pady=5)
		
		self.progress_percentage_label = ttk.Label(progress_info, text="0%", 
												  font=("Arial", 11, "bold"))
		self.progress_percentage_label.pack(side=tk.LEFT)
		
		self.progress_iteration_label = ttk.Label(progress_info, text="(0/0)")
		self.progress_iteration_label.pack(side=tk.LEFT, padx=(5, 0))
		
		self.progress_eta_label = ttk.Label(progress_info, text="")
		self.progress_eta_label.pack(side=tk.RIGHT)
		
		# Progress bar
		self.progress_var = tk.DoubleVar()
		self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
										  maximum=100, style="Custom.Horizontal.TProgressbar")
		self.progress_bar.pack(fill=tk.X, pady=5)
		
		# Status and speed
		status_info = ttk.Frame(progress_frame)
		status_info.pack(fill=tk.X)
		
		self.iteration_status_label = ttk.Label(status_info, text="Status: Idle")
		self.iteration_status_label.pack(side=tk.LEFT)
		
		self.speed_label = ttk.Label(status_info, text="")
		self.speed_label.pack(side=tk.RIGHT)
		
		# Statistics section
		stats_frame = ttk.LabelFrame(main_container, text="Statistics", padding=10)
		stats_frame.pack(fill=tk.X, pady=(0, 10))
		
		# Counters
		counters = ttk.Frame(stats_frame)
		counters.pack(fill=tk.X)
		
		self.pass_count_label = ttk.Label(counters, text="✓ Pass: 0", foreground="green")
		self.pass_count_label.pack(side=tk.LEFT)
		
		self.fail_count_label = ttk.Label(counters, text="✗ Fail: 0", foreground="red")
		self.fail_count_label.pack(side=tk.LEFT, padx=(10, 0))
		
		self.skip_count_label = ttk.Label(counters, text="⊘ Skip: 0", foreground="orange")
		self.skip_count_label.pack(side=tk.LEFT, padx=(10, 0))
		
		self.elapsed_time_label = ttk.Label(counters, text="Time: 00:00")
		self.elapsed_time_label.pack(side=tk.RIGHT)
		
		# Status Log section
		log_frame = ttk.LabelFrame(main_container, text="Status Log", padding=5)
		log_frame.pack(fill=tk.BOTH, expand=True)
		
		# Log container
		log_container = ttk.Frame(log_frame)
		log_container.pack(fill=tk.BOTH, expand=True)
		
		# Text widget with scrollbar
		self.status_log = tk.Text(log_container, bg="black", fg="white", 
								 font=("Consolas", 10), wrap=tk.WORD, 
								 state=tk.DISABLED, width=45, height=15,
								 insertbackground="white",  # Cursor color
							 	 selectbackground="darkblue",  # Selection background
							 	 selectforeground="white")  # Selection text color)
		
		log_scrollbar = ttk.Scrollbar(log_container, orient="vertical", 
									 command=self.status_log.yview)
		self.status_log.configure(yscrollcommand=log_scrollbar.set)
		
		self.status_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		
		# Log controls
		log_controls = ttk.Frame(log_frame)
		log_controls.pack(fill=tk.X, pady=(5, 0))
		
		ttk.Button(log_controls, text="Clear", 
				  command=self.clear_status_log).pack(side=tk.LEFT)
		ttk.Button(log_controls, text="Save", 
				  command=self.save_status_log).pack(side=tk.LEFT, padx=(5, 0))
		
		self.auto_scroll_var = tk.BooleanVar(value=True)
		ttk.Checkbutton(log_controls, text="Auto-scroll", 
					   variable=self.auto_scroll_var).pack(side=tk.RIGHT)
		
		# Initialize tracking variables
		self.start_time = None
		self.last_iteration_time = None
		self.pass_count = 0
		self.fail_count = 0
		self.skip_count = 0
		
		# Add initial messages
		self.log_status("Framework Control Panel initialized")
		self.log_status("Ready to load experiments...")	

	def update_progress_display(self, experiment_name="", strategy_type="", test_name="", 
							  status="Idle", result_status=None):
		"""Update the enhanced progress display"""
		# Update basic labels only if provided
		if experiment_name is not None:
			self.strategy_label.configure(text=f"Experiment: {experiment_name}")
		if strategy_type:
			self.test_name_label.configure(text=f"Strategy: {strategy_type} - {test_name}")
		if status:
			self.iteration_status_label.configure(text=f"Status: {status}")
		
		# Update counters if result status is provided
		if result_status:
			if result_status.upper() in ["PASS", "SUCCESS", "*"]:
				self.pass_count += 1
			elif result_status.upper() in ["FAIL", "FAILED", "ERROR"]:
				self.fail_count += 1
			else:
				self.skip_count += 1
			
			self.pass_count_label.configure(text=f"✓ Pass: {self.pass_count}")
			self.fail_count_label.configure(text=f"✗ Fail: {self.fail_count}")
			self.skip_count_label.configure(text=f"⊘ Skip: {self.skip_count}")
		
		# Update timing and speed calculations
		self._update_timing_display()

	def _update_timing_display(self):
		"""Update timing display including elapsed time, ETA, and speed"""
		current_time = time.time()
		
		# Initialize start time if not set
		if self.start_time is None:
			self.start_time = current_time
		
		# Calculate elapsed time
		elapsed_seconds = current_time - self.start_time
		elapsed_str = self._format_time(elapsed_seconds)
		self.elapsed_time_label.configure(text=f"Time: {elapsed_str}")
		
		# Calculate and display speed/ETA if we have progress data
		if hasattr(self, 'current_iteration') and hasattr(self, 'total_iterations_in_experiment'):
			self._update_speed_and_eta(current_time, elapsed_seconds)

	def _update_speed_and_eta(self, current_time, elapsed_seconds):
		"""Update speed and ETA calculations"""
		try:
			# Calculate total completed iterations across all experiments
			total_completed = (self.current_experiment_index * 
							getattr(self, 'avg_iterations_per_experiment', 10) + 
							max(0, self.current_iteration - 1))
			
			# Calculate total expected iterations
			total_expected = (self.total_experiments * 
							getattr(self, 'avg_iterations_per_experiment', 10))
			
			if total_completed > 0 and elapsed_seconds > 0:
				# Calculate iterations per second
				iterations_per_second = total_completed / elapsed_seconds
				
				# Update speed display
				if iterations_per_second >= 1:
					speed_text = f"{iterations_per_second:.1f} iter/s"
				else:
					seconds_per_iteration = elapsed_seconds / total_completed
					speed_text = f"{seconds_per_iteration:.1f} s/iter"
				
				self.speed_label.configure(text=speed_text)
				
				# Calculate ETA
				remaining_iterations = total_expected - total_completed
				if remaining_iterations > 0 and iterations_per_second > 0:
					eta_seconds = remaining_iterations / iterations_per_second
					eta_str = self._format_time(eta_seconds)
					self.progress_eta_label.configure(text=f"ETA: {eta_str}")
				else:
					self.progress_eta_label.configure(text="ETA: --:--")
			else:
				self.speed_label.configure(text="")
				self.progress_eta_label.configure(text="")
				
		except Exception as e:
			# Don't let timing calculations break the UI
			print(f"Error updating speed/ETA: {e}")

	def _format_time(self, seconds):
		"""Format seconds into HH:MM:SS or MM:SS format"""
		if seconds < 0:
			return "00:00"
		
		hours = int(seconds // 3600)
		minutes = int((seconds % 3600) // 60)
		seconds = int(seconds % 60)
		
		if hours > 0:
			return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
		else:
			return f"{minutes:02d}:{seconds:02d}"

	def _estimate_iterations_per_experiment(self):
		"""Estimate average iterations per experiment for timing calculations"""
		if not self.experiments:
			return 10  # Default estimate
		
		total_iterations = 0
		experiment_count = 0
		
		for experiment_data in self.experiments.values():
			test_type = experiment_data.get('Test Type', '')
			
			if test_type == 'Loops':
				iterations = experiment_data.get('Loops', 5)
			elif test_type == 'Sweep':
				# Calculate sweep iterations
				start = experiment_data.get('Start', 0)
				end = experiment_data.get('End', 10)
				step = experiment_data.get('Steps', 1)
				iterations = max(1, int((end - start) / step) + 1)
			elif test_type == 'Shmoo':
				# Estimate shmoo iterations (this would need more complex calculation)
				iterations = 25  # Default estimate for shmoo
			else:
				iterations = 5  # Default
			
			total_iterations += iterations
			experiment_count += 1
		
		avg_iterations = total_iterations / experiment_count if experiment_count > 0 else 10
		self.avg_iterations_per_experiment = avg_iterations

		return avg_iterations

	def reset_timing(self):
		"""Reset timing calculations for new test run"""
		self.start_time = None
		self.last_iteration_time = None
		
	def reset_progress_tracking(self):
		"""Reset progress tracking variables"""
		self.start_time = None
		self.last_iteration_time = None
		self.pass_count = 0
		self.fail_count = 0
		self.skip_count = 0
		
		# Reset display
		self.pass_count_label.configure(text="✓ Pass: 0")
		self.fail_count_label.configure(text="✗ Fail: 0")
		self.skip_count_label.configure(text="⊘ Skip: 0")
		self.elapsed_time_label.configure(text="Time: 00:00")
		self.progress_eta_label.configure(text="")
		self.speed_label.configure(text="")

	def clear_status_log(self):
		"""Clear the status log"""
		self.status_log.configure(state=tk.NORMAL)
		self.status_log.delete("1.0", tk.END)
		self.status_log.configure(state=tk.DISABLED)
		self.log_status("Status log cleared")

	def save_status_log(self):
		"""Save status log to file"""
		try:
			from tkinter import filedialog
			file_path = filedialog.asksaveasfilename(
				defaultextension=".txt",
				filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
				title="Save Status Log"
			)
			if file_path:
				log_content = self.status_log.get("1.0", tk.END)
				with open(file_path, 'w') as f:
					f.write(log_content)
				self.log_status(f"Status log saved to: {file_path}")
		except Exception as e:
			self.log_status(f"Error saving log: {str(e)}")

	def log_status(self, message):
		"""Add message to status log with timestamp"""
		timestamp = datetime.now().strftime("%H:%M:%S")
		log_message = f"[{timestamp}] {message}\n"
		
		self.status_log.configure(state=tk.NORMAL)
		self.status_log.insert(tk.END, log_message)
		
		# Auto-scroll if enabled
		if self.auto_scroll_var.get():
			self.status_log.see(tk.END)
			
		self.status_log.configure(state=tk.DISABLED)
		
		# Keep only last 200 lines to prevent memory issues
		lines = self.status_log.get("1.0", tk.END).split('\n')
		if len(lines) > 200:
			self.status_log.configure(state=tk.NORMAL)
			self.status_log.delete("1.0", f"{len(lines)-200}.0")
			self.status_log.configure(state=tk.DISABLED)
		
	def _reset_end_button_after_completion(self):
		"""Reset END button after experiment completion"""
		try:
			self.end_button.configure(text="End", style="End.TButton", state=tk.DISABLED)
			self.log_status("END command state cleared - ready for next experiment")
		except Exception as e:
			print(f"Error resetting END button: {e}")

	def _update_overall_progress(self):
		"""Calculate and update overall progress based on experiments and iterations"""
		if self.total_experiments == 0:
			self.progress_var.set(0)
			return
		
		# Calculate progress within current experiment
		if self.total_iterations_in_experiment > 0:
			# Progress from completed iterations
			completed_iterations_progress = (self.current_iteration - 1) / self.total_iterations_in_experiment
			
			# Progress from current iteration
			current_iteration_progress = self.current_iteration_progress / self.total_iterations_in_experiment
				
			# Total progress within current experiment (0.0 to 1.0)
			experiment_progress = min(1.0, completed_iterations_progress + current_iteration_progress)
		else:
			experiment_progress = 0.0
		
		# Calculate overall progress across all experiments
		if self.total_experiments > 0:
			# Progress from completed experiments
			completed_experiments_progress = self.current_experiment_index / self.total_experiments
			
			# Progress from current experiment
			current_experiment_contribution = experiment_progress / self.total_experiments
			
			# Total overall progress
			overall_progress = (completed_experiments_progress + current_experiment_contribution) * 100
		else:
			overall_progress = 0.0
		
		# Update progress bar
		self.progress_var.set(min(100, max(0, overall_progress)))
		
		# Update progress labels
		self.progress_percentage_label.configure(text=f"{int(overall_progress)}%")
		
		# Update iteration info
		if self.current_experiment_name:
			iteration_text = f"Exp {self.current_experiment_index + 1}/{self.total_experiments} - Iter {self.current_iteration}/{self.total_iterations_in_experiment}"
		else:
			iteration_text = f"Exp {self.current_experiment_index}/{self.total_experiments}"
		
		self.progress_iteration_label.configure(text=iteration_text)

	
		# Debug logging
		#print(f"DEBUG Progress: {overall_progress:.1f}% (Exp: {self.current_experiment_index+1}/{self.total_experiments}, Iter: {self.current_iteration}/{self.total_iterations_in_experiment}, Weight: {self.current_iteration_progress:.2f})")

	def _display_experiment_summary(self, summary_data):
		"""Display experiment summary in status log"""
		self.log_status("=" * 40)
		self.log_status(f"SUMMARY: {summary_data['test_name']}")
		self.log_status("=" * 40)
		self.log_status(f"Strategy: {summary_data['strategy_type']}")
		self.log_status(f"Total Tests: {summary_data['total_tests']}")
		self.log_status(f"Success Rate: {summary_data['success_rate']}%")
		
		# Display status breakdown
		self.log_status("Status Breakdown:")
		for status, count in summary_data['status_counts'].items():
			percentage = (count / summary_data['total_tests'] * 100) if summary_data['total_tests'] > 0 else 0
			self.log_status(f"  {status}: {count} ({percentage:.1f}%)")
		
		# Display failure patterns if any
		if summary_data['failure_patterns']:
			self.log_status("Top Failure Patterns:")
			for pattern, count in list(summary_data['failure_patterns'].items())[:3]:
				self.log_status(f"  {pattern}: {count} occurrences")
		
		if summary_data['first_fail_iteration']:
			self.log_status(f"First Failure: Iteration {summary_data['first_fail_iteration']}")
		
		execution_time = summary_data.get('execution_time', 0)
		if execution_time > 0:
			self.log_status(f"Execution Time: {execution_time:.1f} seconds")
		
		self.log_status("=" * 40)
		
	def create_status_log(self):
		"""Create status log widget at the bottom"""
		# Separator
		tk.Frame(self.root, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=10, pady=5)
		
		# Log frame
		log_frame = tk.Frame(self.root)
		log_frame.pack(fill=tk.X, padx=10, pady=5)
		
		tk.Label(log_frame, text="Status Log:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
		
		# Create text widget with scrollbar
		log_container = tk.Frame(log_frame)
		log_container.pack(fill=tk.X, pady=(5, 0))
		
		self.status_log = tk.Text(log_container, height=6, bg="black", fg="white", 
								 font=("Consolas", 9), wrap=tk.WORD, state=tk.DISABLED)
		
		scrollbar = tk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.status_log.yview)
		self.status_log.configure(yscrollcommand=scrollbar.set)
		
		self.status_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		
		# Add initial message
		self.log_status("Framework Control Panel initialized")

	def open_settings_window(self):
		SettingsWindow(self.root, self.S2T_CONFIG, self.update_configuration)

	def open_power_control_window(self):
		PowerControlWindow(self.root, self.Framework)

	def open_mask_management(self):
		MaskManagementWindow(self.root, self.mask_dict, self.update_mask_dict, self.Framework)

	def update_mask_dict(self, updated_mask_dict):
		
		print('Updating Masking Data with new Entry:')
		print(f'Old: {self.mask_dict.keys()}')
		self.mask_dict = updated_mask_dict
		print(f'New: {self.mask_dict.keys()}')
		self.refresh_experiment_rows()

	def refresh_experiment_rows(self):
		for frame, run_label, enabled_var, data, mask_var, experiment in self.experiment_frames:
			mask_dropdown = frame.winfo_children()[-2]  # Assuming mask dropdown is second last widget
			mask_dropdown['menu'].delete(0, 'end')
			for mask_name in self.mask_dict.keys():
				mask_dropdown['menu'].add_command(label=mask_name, command=lambda value=mask_name, d=data, mv=mask_var, e=experiment: self.update_mask(value, d, mv, e))

	def check_ipc(self):
		if self.Framework:
			self.Framework.refresh_ipc()
		else:
			print('Refreshing SV and Unlocking IPC')

	def update_configuration(self, updated_config):
		
		self.S2T_CONFIG = updated_config
		print("Configuration updated:", self.S2T_CONFIG)

	def load_experiments_file(self):
		file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("JSON files", "*.json")])
		if file_path:
			self.file_entry.delete(0, tk.END)
			self.file_entry.insert(0, file_path)
			self.load_experiments(file_path)
	
	def load_experiments(self, file_path):
		#try:
		
		self.experiments = OpenExperiment(file_path) if self.Framework == None else self.Framework.Recipes(file_path)
		self.saveas_button.configure(state=tk.NORMAL)

		# Estimate iterations per experiment for timing calculations
		self._estimate_iterations_per_experiment()

		self.create_experiment_rows()

		#except Exception as e:
		#    messagebox.showerror("Error", f"Failed to load experiments: {e}")

	def create_experiment_header(self):
		"""Create header row for experiment columns"""
		if hasattr(self, 'header_frame'):
			self.header_frame.destroy()
		
		# Header frame
		self.header_frame = ttk.Frame(self.experiment_container, style="Header.TFrame")
		self.header_frame.pack(fill=tk.X, pady=(0, 5), padx=2)
		
		# Configure grid weights
		self.header_frame.grid_columnconfigure(2, weight=1)
		
		# Header labels
		headers = [
			("", 0, 3),  # Checkbox column
			("Experiment", 1, 15),
			("Test Name", 2, 20),
			("Mode", 3, 8),
			("Type", 4, 8),
			("Edit", 5, 6),  # Edit button
			("Mask", 6, 10),
			("Status", 7, 12)
		]
		
		for text, col, width in headers:
			if text:  # Only create label if there's text
				label = ttk.Label(self.header_frame, text=text, font=("Arial", 9, "bold"))
				if col == 2:  # Test name column
					label.grid(row=0, column=col, sticky="ew", padx=(0, 8))
				else:
					label.grid(row=0, column=col, sticky="w", padx=(0, 8))
		
		# Add separator line
		separator = ttk.Separator(self.experiment_container, orient='horizontal')
		separator.pack(fill=tk.X, pady=(0, 5))
		
	def create_experiment_rows(self):
		"""Create experiment rows with thread-safe data storage"""
		# Clear existing frames
		for frame_data in getattr(self, 'experiment_frames', []):
			try:
				if isinstance(frame_data, dict) and 'frame' in frame_data:
					frame_data['frame'].destroy()
				elif hasattr(frame_data, '__len__') and len(frame_data) > 0:
					# Handle old tuple format
					frame_data[0].destroy()
			except Exception as e:
				print(f"Error destroying frame: {e}")
		
		self.experiment_frames = []
		
		if not self.experiments:
			return
		
		# Initialize experiment states if not exists
		if not hasattr(self, 'experiment_states'):
			self.experiment_states = {}
		
		# Calculate column widths based on content
		max_exp_name_width = max(len(name) for name in self.experiments.keys()) + 2
		max_test_name_width = max(len(data.get('Test Name', '')) for data in self.experiments.values()) + 2
		
		# Ensure minimum widths
		exp_name_width = max(15, min(25, max_exp_name_width))
		test_name_width = max(20, min(40, max_test_name_width))
		
		for experiment_name, experiment_data in self.experiments.items():
			data = experiment_data
			
			# Store state as primitive data, not Tkinter variables
			enabled_status = data.get('Experiment', "Disabled").lower() == 'enabled'
			self.experiment_states[experiment_name] = enabled_status
			
			# Main experiment frame - use ttk.Frame for consistent theming
			frame = ttk.Frame(self.experiment_container, padding=(5, 2))
			frame.pack(fill=tk.X, pady=1, padx=2)
			
			# Configure grid weights for proper expansion
			frame.grid_columnconfigure(2, weight=1)  # Test name column expands
			
			# Create Tkinter variable for UI only (not passed to threads)
			enabled_var = tk.BooleanVar(value=enabled_status)
			
			# Checkbox with lambda that captures experiment_name
			checkbox = ttk.Checkbutton(frame, variable=enabled_var, 
									command=lambda name=experiment_name, var=enabled_var: 
									self._update_experiment_state(name, var.get()))
			checkbox.grid(row=0, column=0, sticky="w", padx=(0, 8))
			
			# Experiment name - fixed width based on content
			name_label = ttk.Label(frame, text=experiment_name, width=exp_name_width, 
								font=("Arial", 9))
			name_label.grid(row=0, column=1, sticky="w", padx=(0, 8))
			
			# Test name (expandable) - minimum width based on content
			test_name_text = data.get('Test Name', '')
			test_name_label = ttk.Label(frame, text=test_name_text, width=test_name_width, 
									font=("Arial", 9), foreground="blue")
			test_name_label.grid(row=0, column=2, sticky="ew", padx=(0, 8))
			
			# Test mode
			mode_label = ttk.Label(frame, text=data.get('Test Mode', ''), width=8,
								font=("Arial", 9))
			mode_label.grid(row=0, column=3, sticky="w", padx=(0, 8))
			
			# Test type
			type_label = ttk.Label(frame, text=data.get('Test Type', ''), width=8,
								font=("Arial", 9))
			type_label.grid(row=0, column=4, sticky="w", padx=(0, 8))
			
			# Edit button
			edit_button = ttk.Button(frame, text="Edit", width=6,
								command=lambda d=data: self.edit_experiment(d))
			edit_button.grid(row=0, column=5, sticky="w", padx=(0, 8))
			
			# Mask dropdown - store mask selection in experiment_states
			mask_var = tk.StringVar()
			mask_dropdown = ttk.Combobox(frame, textvariable=mask_var, 
									values=list(self.mask_dict.keys()), 
									width=10, state="readonly", font=("Arial", 8))
			mask_dropdown.grid(row=0, column=6, sticky="w", padx=(0, 8))
			mask_dropdown.bind('<<ComboboxSelected>>', 
							lambda e, d=data, mv=mask_var, en=experiment_name: 
							self.update_mask(mv.get(), d, mv, en))
			
			# Status label - Use tk.Label for color support
			run_label = tk.Label(frame, text="Idle", bg="lightgray", fg="black", 
							width=12, relief=tk.GROOVE, borderwidth=1,
							font=("Arial", 8))
			run_label.grid(row=0, column=7, sticky="ew", padx=(8, 0))
			
			# Store frame data in new format (dict instead of tuple)
			frame_data = {
				'frame': frame,
				'run_label': run_label,
				'enabled_var': enabled_var,  # Keep for UI updates only
				'data': data,
				'mask_var': mask_var,
				'experiment_name': experiment_name,
				'checkbox': checkbox,
				'name_label': name_label,
				'test_name_label': test_name_label,
				'mode_label': mode_label,
				'type_label': type_label,
				'edit_button': edit_button,
				'mask_dropdown': mask_dropdown
			}
			
			self.experiment_frames.append(frame_data)
			
			# Update widget states based on enabled status
			self.toggle_experiment(frame_data, enabled_status)
		
		# Update scroll region after adding all experiments
		self.root.after(10, lambda: self._update_scroll_region(self.experiment_canvas))
		
		# Auto-size window after loading experiments
		self.root.after(100, self.auto_size_window)

	# Method for thread-safe state updates
	def _update_experiment_state(self, experiment_name: str, enabled: bool):
		"""Update experiment state thread-safely"""
		self.experiment_states[experiment_name] = enabled
		# Update the data
		if experiment_name in self.experiments:
			self.experiments[experiment_name]['Experiment'] = 'Enabled' if enabled else 'Disabled'
		
		# Log the change
		status = "enabled" if enabled else "disabled"
		self.log_status(f"Experiment '{experiment_name}' {status}")

	def update_mask(self, selected_mask, data, mask_var, experiment):
		if selected_mask == "Default":
			data['External Mask'] = None
		else:
			data['External Mask'] = self.mask_dict[selected_mask]
		mask_var.set(selected_mask) 
		print(f"Experiment External Mask --> {experiment}::{selected_mask}")
		print(f"\tValue --> {data['External Mask']}")

	def toggle_experiment(self, frame_data, enabled_status):
		"""Toggle experiment widgets based on enabled status"""
		try:
			state = tk.NORMAL if enabled_status else tk.DISABLED
			
			# Update all widgets except checkbox
			widgets_to_update = ['name_label', 'test_name_label', 'mode_label', 
							'type_label', 'edit_button', 'mask_dropdown']
			
			for widget_name in widgets_to_update:
				if widget_name in frame_data:
					try:
						frame_data[widget_name].configure(state=state)
					except Exception as e:
						print(f"Error updating {widget_name}: {e}")
						
		except Exception as e:
			print(f"Error in toggle_experiment: {e}")
	
	def edit_experiment(self, data):
		EditExperimentWindow2(self.root, data, self.update_experiment)

	def update_experiment(self, updated_data):
		# Update the experiment data and refresh the display
		for frame, run_label, enabled_var, data, mask_var, experiment_name in self.experiment_frames:
			if data == updated_data:
				# Update the display with new data
				enabled_status = updated_data.get('Experiment', "Disabled").lower() == 'enabled'
				enabled_var.set(enabled_status)
				#frame.winfo_children()[1].configure(text=updated_data.get('Test Name', ''))
				frame.winfo_children()[2].configure(text=updated_data.get('Test Name', ''))
				frame.winfo_children()[3].configure(text=updated_data.get('Test Mode', ''))
				frame.winfo_children()[4].configure(text=updated_data.get('Test Type', ''))
				break

	def update_unit_data(self):
		if self.Framework != None and self.check_unit_data_var.get():
			self.Framework.update_unit_data()

	def upload_data_to_db(self):
		if self.upload_unit_data_var.get():
			self.upload_unit_data = True
		else:
			self.upload_unit_data = False
		
		if self.Framework != None:
			self.Framework.upload_to_database = self.upload_unit_data

	def test_ttl(self, ):
		#self.Framework.Test_Macros(self.root, self.experiments)
		TestTTLWindow(self.root, self.experiments, self.Framework)
		#EditExperimentWindow(self.root, data)
		#pass

	def _create_primitive_experiment_data(self, experiment_name):
		"""Create primitive data copy for thread safety"""
		original_data = self.experiments[experiment_name]
		exp_data = {}
		
		# Copy all primitive data
		for key, value in original_data.items():
			if isinstance(value, (str, int, float, bool, list, dict, type(None))):
				exp_data[key] = value
			else:
				exp_data[key] = str(value)
		
		# Add experiment name for identification
		exp_data['experiment_name'] = experiment_name
		
		# Add mask data if available
		external_mask = original_data.get('External Mask')
		if external_mask is not None:
			exp_data['External Mask'] = external_mask
		
		return exp_data

	def _simulate_test_execution(self, exp_data):
		"""Simulate test execution for testing purposes"""
		import random
		time.sleep(random.uniform(2, 5))  # Simulate work
		return random.choice([True, True, True, False])  # 75% success rate

	def _estimate_experiment_iterations(self, exp_data):
		"""Estimate number of iterations for an experiment"""
		test_type = exp_data.get('Test Type', '')
		
		if test_type == 'Loops':
			return exp_data.get('Loops', 5)
		elif test_type == 'Sweep':
			start = exp_data.get('Start', 0)
			end = exp_data.get('End', 10)
			step = exp_data.get('Steps', 1)
			return max(1, int((end - start) / step) + 1)
		elif test_type == 'Shmoo':
			return 25  # Default estimate
		else:
			return 5
			
	def debug_progress_state(self):
		"""Enhanced debug method to track experiment counting"""
		
		if not debug:
			return
		
		try:
			print("=== PROGRESS DEBUG ===")
			print(f"Progress Bar Value: {self.progress_var.get()}")
			print(f"Current Experiment Index: {self.current_experiment_index}")
			print(f"Total Experiments: {self.total_experiments}")
			print(f"Current Experiment: {self.current_experiment_index + 1}/{self.total_experiments}")
			print(f"Current Iteration: {self.current_iteration}/{self.total_iterations_in_experiment}")
			print(f"Iteration Progress Weight: {self.current_iteration_progress}")
			print(f"Experiment Name: {self.current_experiment_name}")
			
			# Calculate what progress should be
			if self.total_experiments > 0:
				exp_progress = self.current_experiment_index / self.total_experiments
				iter_progress = 0
				if self.total_iterations_in_experiment > 0:
					iter_progress = ((self.current_iteration - 1) + self.current_iteration_progress) / self.total_iterations_in_experiment
				
				overall_progress = (exp_progress + (iter_progress / self.total_experiments)) * 100
				print(f"CALCULATED Progress: {overall_progress:.1f}%")
				print(f"  Exp Progress: {exp_progress:.3f}")
				print(f"  Iter Progress: {iter_progress:.3f}")

			print("======================")
		except Exception as e:
			print(f"Debug error: {e}")

	def _update_ui_for_start(self):
		"""Update UI elements for execution start"""
		try:
			self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")
			self.log_status("Starting test execution")
			
			# Reset run labels
			for frame_data in self.experiment_frames:
				frame_data['run_label'].configure(text="Idle", bg="white", fg="black")
			
			# Update button states
			self.run_button.configure(state=tk.DISABLED)
			self.cancel_button.configure(state=tk.NORMAL)
			self.end_button.configure(state=tk.NORMAL, text="End", style="End.TButton")
			self.hold_button.configure(state=tk.NORMAL, text=" Hold ", style="Hold.TButton")
			self.power_control_button.configure(state=tk.DISABLED)
			self.ipc_control_button.configure(state=tk.DISABLED)
			
		except Exception as e:
			print(f"Error updating UI for start: {e}")

	def _ensure_previous_execution_stopped(self):
		"""Ensure any previous execution is completely stopped"""
		if hasattr(self, 'test_thread') and self.test_thread and self.test_thread.is_alive():
			self.cancel_requested.set()
			
			# Give it time to stop gracefully
			self.test_thread.join(timeout=3.0)
			
			if self.test_thread.is_alive():
				self.log_status("Warning: Previous thread did not stop gracefully")
		
		# Reset framework execution state
		self.framework_execution_active = False
		self.current_framework_thread = None
		
		# Clear the cancel flag for new execution
		self.cancel_requested.clear()

	def _update_ui_for_execution_start(self):
		"""Update UI elements for execution start"""
		self.status_label.configure(text=" Running ", bg="#BF0000", fg="white")
		self.log_status("Starting test execution")
		
		# Reset run labels
		for _, run_label, _, _, _, _ in self.experiment_frames:
			run_label.configure(text="Idle", bg="white", fg="black")
		
		# Update button states
		self.run_button.configure(state=tk.DISABLED)
		self.cancel_button.configure(state=tk.NORMAL)
		self.end_button.configure(state=tk.NORMAL, text="End", style="End.TButton")
		self.hold_button.configure(state=tk.NORMAL, text=" Hold ", style="Hold.TButton")
		self.power_control_button.configure(state=tk.DISABLED)
		self.ipc_control_button.configure(state=tk.DISABLED)
		
	def _reset_end_command_state(self):
		"""Reset END command state for new execution"""
		try:
			# Reset Framework END flags
			if self.Framework:
				if hasattr(self.Framework, '_end_experiment_flag'):
					self.Framework._end_experiment_flag.clear()
				if hasattr(self.Framework, '_current_execution_state'):
					self.Framework._current_execution_state['end_requested'] = False
			
			# Reset local END state
			if hasattr(self, 'end_after_current'):
				self.end_after_current = False
			
			# Reset END button appearance
			self.end_button.configure(text="End", style="End.TButton", state=tk.NORMAL)
			
			self.log_status("END command state reset for new execution")
			
		except Exception as e:
			self.log_status(f"Error resetting END command state: {e}")

	def _update_ui_after_cancel(self):
		"""Update UI after cancellation - called from main thread"""
		try:
			self.status_label.configure(text=" Cancelled ", bg="gray", fg="white")
			self.run_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text=" Hold ")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.power_control_button.configure(state=tk.NORMAL)
			self.ipc_control_button.configure(state=tk.NORMAL)
			
			self.log_status("UI updated after cancellation")
				
		except Exception as e:
			print(f"Error updating UI after cancel: {e}")

	def _update_ui_after_end(self):
		"""Update UI after END command - called from main thread"""
		try:
			self.status_label.configure(text=" Ended ", bg="orange", fg="white")
			self.run_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text=" Hold ")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.power_control_button.configure(state=tk.NORMAL)
			self.ipc_control_button.configure(state=tk.NORMAL)
			
			self.log_status("UI updated after END command")
				
		except Exception as e:
			print(f"Error updating UI after end: {e}")

	def _update_ui_after_completion(self):
		"""Update UI after normal completion - called from main thread"""
		try:
			if not self.hold_active and self.current_experiment_index >= len(self.experiment_frames):
				self.status_label.configure(text=" Completed ", bg="#006400", fg="white")
				self.log_status("All experiments completed")

			# Enable Run button and disable Cancel and Hold buttons
			self.run_button.configure(state=tk.NORMAL)
			self.cancel_button.configure(state=tk.DISABLED)
			self.hold_button.configure(state=tk.DISABLED, text=" Hold ")
			self.end_button.configure(state=tk.DISABLED, text="End", style="End.TButton")
			self.power_control_button.configure(state=tk.NORMAL)
			self.ipc_control_button.configure(state=tk.NORMAL)
			
			self.log_status("UI updated after completion")
				
		except Exception as e:
			print(f"Error updating UI after completion: {e}")
			
	def _reset_end_state_after_completion(self):
	
		"""Reset END command state after test completion"""
		try:
			# Reset Framework END state
			if self.Framework:
				if hasattr(self.Framework, '_end_experiment_flag'):
					self.Framework._end_experiment_flag.clear()
				if hasattr(self.Framework, '_current_execution_state'):
					self.Framework._current_execution_state['end_requested'] = False
			
			# Reset local END state
			if hasattr(self, 'end_after_current'):
				self.end_after_current = False
			
			self.log_status("END command state cleared after test completion")
			
		except Exception as e:
			self.log_status(f"Error resetting END state: {e}")

	# Not Used
	def toggle_hold(self):
		self.hold_active = not self.hold_active
		if self.hold_active:
			self.hold_button.configure(bg="orange")
		else:
			self.hold_button.configure(bg="SystemButtonFace")
	
	# Not Used
	def hold_tests(self):
		# Implement the logic to hold tests
		pass
					
	# Not used -- check and remove
	def _cancel_framework_with_timeout(self):
		"""Cancel framework execution with timeout (runs in separate thread)"""
		try:
			# Give framework time to cancel gracefully
			if self.Framework:
				self.Framework.cancel_execution()
				
			# Wait a bit for cleanup
			time.sleep(1.0)
			
			# Update UI from main thread
			self.root.after(0, lambda: self.log_status("Framework cancellation completed"))
			
		except Exception as e:
			# Update UI from main thread
			emessage = f"Framework cancellation error: {e}"
			self.root.after(0, lambda: self.log_status(emessage))

	# Not used -- check and remove
	def _reset_ui_after_cancel(self):
		"""Reset UI elements after cancellation"""
		try:
			self.hold_button.configure(bg="SystemButtonFace", text=" Hold ")
			self.end_button.configure(text="End", style="End.TButton")
			
			if hasattr(self, 'end_after_current'):
				self.end_after_current = False
				
			# Schedule status reset
			self.root.after(1000, lambda: self.status_label.configure(text=" Ready ", bg="white", fg="black"))
			
		except Exception as e:
			print(f"Error resetting UI: {e}")
						
	def save_config(self):
		# Open a dialog to select the save location
		file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
		if file_path:
			Convert_xlsx_to_json(file_path, self.experiments)

class SettingsWindow:
	def __init__(self, parent, config, update_callback):
		self.top = tk.Toplevel(parent)
		self.top.title("Settings")
		
		self.config = config
		self.entries = {}
		self.update_callback = update_callback

		self.create_widgets()

	def create_widgets(self):
		row = 0
		for label, key in CONFIG_LABELS.items():
			tk.Label(self.top, text=label).grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
			entry = tk.Entry(self.top, width=20)
			entry.grid(row=row, column=1, padx=10, pady=5)
			# Display hex values for specific keys
			if key in ['AFTER_MRC_POST', 'EFI_POST', 'LINUX_POST']:
				entry.insert(0, f"{self.config[key]:#0x}")
			else:
				entry.insert(0, str(self.config[key]))
			self.entries[key] = entry
			row += 1
		tk.Button(self.top, text="Save", command=self.save_changes).grid(row=row, column=0, columnspan=2, pady=10)

	def save_changes(self):
		for key, entry in self.entries.items():
			try:
				# Convert hex input for specific keys
				if key in ['AFTER_MRC_POST', 'EFI_POST', 'LINUX_POST']:
					self.config[key] = int(entry.get(), 16)
				else:
					self.config[key] = int(entry.get())
			except ValueError:
				messagebox.showerror("Invalid Input", f"Invalid value for {key}. Please enter a valid integer.")
				return
		self.update_callback(self.config)
		self.top.destroy()
		
class EditExperimentWindow:
	def __init__(self, parent, data, update_callback):
		self.top = tk.Toplevel(parent)
		self.data = data
		title = f"Edit - {self.data['Test Name']}" if self.data else "Edit Experiment"
		self.top.title(title)
		
		
		self.entries = {}
		self.update_callback = update_callback
		self.original_types = {key: type(value) for key, value in data.items()}

		# Create a canvas and a scrollbar
		self.canvas = tk.Canvas(self.top)
		self.scrollbar = tk.Scrollbar(self.top, orient="vertical", command=self.canvas.yview)
		self.scrollable_frame = tk.Frame(self.canvas)

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(
				scrollregion=self.canvas.bbox("all")
			)
		)

		self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=800)
		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		self.scrollbar.pack(side="right", fill="y")
		self.canvas.pack(side="left", fill="both", expand=True)


		self.create_widgets()
	
	def create_widgets(self):
		row = 0
		for key, value in self.data.items():
			
			tk.Label(self.scrollable_frame, text=key).grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
			entry = tk.Entry(self.scrollable_frame, width=100)
			entry.grid(row=row, column=1, columnspan=3, padx=10, pady=5)
			entry.insert(0, str(value) if value is not None else '')
			self.entries[key] = entry
			row += 1
		tk.Button(self.scrollable_frame, text="Save", command=self.save_changes).grid(row=row, column=0, columnspan=2, pady=10)

	
	def save_changes(self):
		for key, entry in self.entries.items():
			original_type = self.original_types[key]
			self.data[key] = self.convert_type(entry.get(), original_type) #if entry.get() != '' else None
		#for key, entry in self.entries.items():
		#	self.data[key] = entry.get() if entry.get() != '' else None
		self.update_callback(self.data)
		self.top.destroy()   

	def convert_type(self, value, original_type):
		if value == ''  or value == 'None':
			return None
		try:
			if original_type is bool:
				return value.lower() in ('true', '1', 'yes')
			return original_type(value)
		except ValueError:
			return value

class EditExperimentWindow2(tk.Toplevel):

	def __init__(self, parent, data, update_callback, config_file='GNRControlPanelConfig.json'):
		super().__init__(parent)
		self.data = data
		self.update_callback = update_callback

		self.config_file = config_file
		
		# Load configuration
		self.load_configuration()

		self.input_vars = {
			key: tk.StringVar(value=str(value) if value is not None else '')
			for key, value in data.items()
		}

		# Initialize widgets and frames
		self.widgets = {}
		self.frames = {}

		container = tk.Frame(self)
		container.pack(fill="both", expand=True)

		self.canvas = tk.Canvas(container)
		self.scrollable_frame = ttk.Frame(self.canvas)

		self.vertical_scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
		self.horizontal_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=self.canvas.xview)

		self.canvas.configure(yscrollcommand=self.vertical_scrollbar.set, xscrollcommand=self.horizontal_scrollbar.set)
		self.vertical_scrollbar.pack(side="right", fill="y")
		self.horizontal_scrollbar.pack(side="bottom", fill="x")
		self.canvas.pack(side="left", fill="both", expand=True)
		self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

		self.scrollable_frame.bind("<Configure>", self.on_frame_configure)

		# Adjust window width for three columns with margin
		column_width = 420  # Estimated width per column
		fixed_width = column_width * 3 + 100  # Margin adjustment
		fixed_height = 800

		self.geometry(f"{fixed_width}x{fixed_height}")

		self.create_form()
		self.create_buttons()
		self.protocol("WM_DELETE_WINDOW", self.on_closing)

	def load_configuration(self):
		current_dir = os.path.dirname(__file__)
		with open(os.path.join(current_dir, self.config_file)) as config_file:
			config_data = json.load(config_file)

		# Convert string type names to actual types
		data_types_with_objects = {}
		type_mapping = {
			"str": str,
			"int": int,
			"float": float,
			"bool": bool,
			"dict":dict
		}
		
		for field, type_list in config_data['data_types'].items():
			data_types_with_objects[field] = [type_mapping[type_name] for type_name in type_list]

		self.data_types = data_types_with_objects
		self.TEST_MODES = config_data['TEST_MODES']
		self.TEST_TYPES = config_data['TEST_TYPES']
		self.VOLTAGE_TYPES=config_data['VOLTAGE_TYPES']
		self.MASK_OPTIONS = config_data['MASK_OPTIONS']
		self.TYPES = config_data['TYPES']
		self.DOMAINS = config_data['DOMAINS']
		self.CONTENT_OPTIONS = config_data['CONTENT_OPTIONS']
		self.CORE_LICENSE_OPTIONS = config_data['CORE_LICENSE_OPTIONS']
		self.fields_to_hide = config_data['fields_to_hide']
		self.field_descriptions = config_data['field_descriptions']
		self.mandatory_fields = config_data['mandatory_fields']
		self.FIELD_GROUPS = config_data['FIELD_GROUPS']
		self.DISABLE_2_CORES_OPTIONS = config_data['DISABLE_2_CORES_OPTIONS']

	def on_frame_configure(self, event):
		self.canvas.configure(scrollregion=self.canvas.bbox("all"))

	def create_form(self):
		self.populate_fields()

	def populate_fields(self, event=None):
		for widget in self.widgets.values():
			for element in widget:
				element.grid_remove()
		self.widgets.clear()
		for frame in self.frames.values():
			frame.grid_remove()
		self.frames.clear()

		frame_row = 0
		frame_col = 0
		selected_type = self.input_vars['Test Type'].get()
		hide_fields = self.fields_to_hide.get(selected_type, [])

		for group_name, fields in self.FIELD_GROUPS.items():
			has_visible_fields = any(field not in hide_fields for field in fields)

			if has_visible_fields:
				style = ttk.Style()
				style.configure("TLabelframe.Label", font=("Arial", 11, "bold"))
				frame = ttk.LabelFrame(
					self.scrollable_frame, text=group_name, padding=(10, 6),
					style="TLabelframe"
				)
				frame.grid(row=frame_row, column=frame_col, sticky='EW', padx=10, pady=5)
				self.frames[group_name] = frame

				row = 0
				for field in fields:
					if field not in hide_fields:
						field_types = self.data_types.get(field, [str])
						entry_widget = None

						if bool in field_types:
							entry_widget = tk.Checkbutton(frame, variable=self.input_vars[field], onvalue='True', offvalue='False')
						elif field in ['Test Type', 'Test Mode', 'Configuration (Mask)', 'Type', 'Domain', 'Core License']:
							options_dict = {
								'Test Mode': self.TEST_MODES, 
								'Test Type': self.TEST_TYPES, 
								'Voltage Type':self.VOLTAGE_TYPES,
								'Configuration (Mask)': self.MASK_OPTIONS, 
								'Type': self.TYPES, 
								'Domain': self.DOMAINS, 
								'Core License': self.CORE_LICENSE_OPTIONS
							}
							options = options_dict[field]
							entry_widget = ttk.Combobox(frame, textvariable=self.input_vars[field], values=options)
							entry_widget.set(self.input_vars[field].get() or options[0])
							if field == 'Test Type':
								entry_widget.bind("<<ComboboxSelected>>", self.populate_fields)
						elif field == 'Content':
							entry_widget = ttk.Combobox(frame, textvariable=self.input_vars[field], values=self.CONTENT_OPTIONS)
							entry_widget.set(self.input_vars[field].get() or self.CONTENT_OPTIONS[0])
						elif field == 'Voltage Type':
							entry_widget = ttk.Combobox(frame, textvariable=self.input_vars[field], values=self.VOLTAGE_TYPES)
							entry_widget.set(self.input_vars[field].get() or self.VOLTAGE_TYPES[0])
						elif field == 'Disable 2 Cores':
							entry_widget = ttk.Combobox(frame, textvariable=self.input_vars[field], values=self.DISABLE_2_CORES_OPTIONS)
							entry_widget.set(self.input_vars[field].get() or self.DISABLE_2_CORES_OPTIONS[0])
						else:
							entry_widget = ttk.Entry(frame, textvariable=self.input_vars[field], width=50)

						if entry_widget:
							label = ttk.Label(frame, text=field)
							label.grid(row=row, column=0, sticky='W', padx=5, pady=5)
							entry_widget.grid(row=row, column=1, sticky='EW', padx=5, pady=5)
							self.create_tooltip(label, self.field_descriptions.get(field, "No description available"))
							self.widgets[field] = (label, entry_widget)
							row += 1

				# Adjust for maximum columns you can fit
				if frame_col == 2:  
					frame_row += 1
					frame_col = 0
				else:
					frame_col += 1

	def create_buttons(self):
		save_button = ttk.Button(self.scrollable_frame, text="Save", command=self.save_changes)
		save_button.grid(row=len(self.frames) + 1, column=0, columnspan=4, pady=10)

	def save_changes(self):
		error_messages = []
		missing_fields = self.highlight_missing_mandatory_fields()
		selected_type = self.input_vars['Test Type'].get()
		hide_fields = self.fields_to_hide.get(selected_type, [])
		validation_errors = self.validate_fields(excluded_fields=hide_fields)

		if missing_fields:
			error_messages.append(f"Missing fields: {', '.join(missing_fields)}")

		if validation_errors:
			error_messages.append("\n".join(validation_errors))

		if error_messages:
			messagebox.showerror("Errors", "\n".join(error_messages))
			return

		current_values = self.get_values()

		for field, original_value in self.data.items():
			new_value_str = current_values.get(field, original_value)
			field_types = self.data_types[field]
			converted_value = None
			for field_type in field_types:
				try:
					if new_value_str is None or new_value_str == '':
						converted_value = None if field not in self.mandatory_fields else original_value
					elif field_type == bool:
						converted_value = new_value_str.lower() == 'true'
					elif field_type == int:
						converted_value = int(new_value_str)
					elif field_type == float:
						converted_value = float(new_value_str)
					elif field_type == str:
						converted_value = str(new_value_str)
					if converted_value is not None:
						self.data[field] = converted_value
						break
				except ValueError:
					continue

			if converted_value is None:
				self.data[field] = original_value

		self.update_callback(self.data)
		self.destroy()

	def get_values(self):
		return {field: (var.get().strip() if var.get() else None) for field, var in self.input_vars.items()}

	def highlight_missing_mandatory_fields(self):
		missing_fields = []
		selected_type = self.input_vars['Test Type'].get()
		hide_fields = self.fields_to_hide.get(selected_type, [])

		for field in self.mandatory_fields + [key for key, val in self.data_types.items() if bool in val]:
			value = self.input_vars[field].get().strip()
			if field not in hide_fields and (not value or value == 'None'):
				self.widgets[field][0].config(foreground="red")
				missing_fields.append(field)

		return missing_fields

	def create_tooltip(self, widget, text):
		def on_enter(event):
			# Use event coordinates to place the tooltip at mouse cursor location
			x = event.x_root + 10  # Slight offset for better visibility
			y = event.y_root + 10
			tooltip = tk.Label(self, text=text, background="lightyellow", relief="solid", borderwidth=1)
			tooltip.place(x=x, y=y)
			widget.tooltip = tooltip

		def on_leave(event):
			if hasattr(widget, 'tooltip'):
				widget.tooltip.destroy()
				del widget.tooltip

		widget.bind("<Enter>", on_enter)
		widget.bind("<Leave>", on_leave)

	def validate_fields(self, excluded_fields=[]):
		error_messages = []

		def is_valid_ip(ip):
			try:
				socket.inet_aton(ip)
				return True
			except socket.error:
				error_messages.append(f"IP Address '{ip}' is invalid")
				return False

		def validate_com_port(value):
			if not value or value == 'None':
				return True
			try:
				port_num = int(value)
				if 0 <= port_num <= 256:
					return True
				error_messages.append(f"COM Port '{value}' is out of range (0-256)")
				return False
			except ValueError:
				error_messages.append(f"COM Port '{value}' is not an integer")
				return False

		def validate_positive_integer(value):
			if not value or value == 'None':
				return True
			if value.isdigit() and int(value) > 0:
				return True
			error_messages.append(f"Test Number '{value}' is not a positive integer")
			return False

		def validate_non_negative_integer(value):
			if not value or value == 'None':
				return True
			if value.isdigit() and int(value) >= 0:
				return True
			error_messages.append(f"Check Core '{value}' is not a non-negative integer")
			return False

		def validate_existing_file(path):
			if not path or path == 'None':
				return True
			if os.path.isfile(path):
				return True
			error_messages.append(f"File '{path}' does not exist")
			return False

		def validate_existing_directory(path):
			if not path or path == 'None':
				return True
			if os.path.isdir(path):
				return True
			error_messages.append(f"Directory '{path}' does not exist")
			return False

		checks = {
			"COM Port": validate_com_port,
			"IP Address": is_valid_ip,
			"Test Number": validate_positive_integer,
			"Test Time": validate_positive_integer,
			"Check Core": validate_non_negative_integer,
			"Scripts File": validate_existing_file,
			"TTL Folder": validate_existing_directory,
			"ShmooFile": validate_existing_file
		}

		selected_type = self.input_vars['Test Type'].get()
		hide_fields = self.fields_to_hide.get(selected_type, [])

		for field, check in checks.items():
			if field in excluded_fields:
				continue

			value = self.input_vars[field].get()
			if not check(value):
				self.widgets[field][0].config(foreground="red")

		return error_messages

class TestTTLWindow:
	def __init__(self, parent, experiments, test_function=None):
		self.top = tk.Toplevel(parent)
		self.top.title("Teraterm Macros Tester (TTL)")
		self.experiments = experiments
		self.test_function = test_function
		self.stop_event = threading.Event()
		self.test_thread = None
		self.exception_queue = queue.Queue()
		self.selected_experiment_name = tk.StringVar()
		self.selected_experiment_name.set(next(iter(experiments)))  # Set default to the first experiment

		self.create_widgets()
		self.update_experiment_info()
		
		# Bind the window close event
		self.top.protocol("WM_DELETE_WINDOW", self.on_close)
	
	def create_widgets(self):
		# Row 1: Select Experiment, Experiment Menu, and Test Button
		tk.Label(self.top, text="Select Experiment", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky=tk.EW)

		self.experiment_menu = tk.OptionMenu(self.top, self.selected_experiment_name, *self.experiments.keys(), command=self.update_experiment_info)
		self.experiment_menu.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

		tk.Button(self.top, text=" Test Macro ", command=self.start_test_thread).grid(row=0, column=2, padx=5, pady=5, sticky=tk.EW)
		tk.Button(self.top, text=" Cancel", command=self.cancel_test).grid(row=0, column=3, padx=5, pady=5, sticky=tk.EW)

		# Row 2: Separator Line
		separator = tk.Frame(self.top, height=2, bd=1, relief=tk.SUNKEN)
		separator.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

		# Row 3: Visual and Content
		self.visual_label = tk.Label(self.top, text="Visual: ")
		self.visual_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

		self.content_label = tk.Label(self.top, text="Content: ")
		self.content_label.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

		tk.Button(self.top, text=" Warm Reset ", command=self.warm_reset).grid(row=2, column=3, padx=5, pady=5, sticky=tk.EW)
		#tk.Button(self.top, text=" Cold Reset ", command=self.reboot_unit).grid(row=2, column=3, padx=5, pady=5, sticky=tk.EW)

		# Row 4: TTL Path
		self.ttl_path_label = tk.Label(self.top, text="TTL Folder: ")
		self.ttl_path_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

		# Row 5: Commands List and Open/Edit TTL Button
		self.ttl_files_listbox = tk.Listbox(self.top)
		self.ttl_files_listbox.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)

		tk.Button(self.top, text=" Open TTL ", command=self.open_edit_ttl_file).grid(row=4, column=2, padx=5, pady=5, sticky=tk.EW)

	def update_experiment_info(self, *args):
		selected_experiment = self.experiments[self.selected_experiment_name.get()]

		self.visual = selected_experiment.get('Visual ID', None)
		self.content = selected_experiment.get('Content', None)
		self.ttl_path = selected_experiment.get('TTL Folder', None)
		self.tnumber = selected_experiment.get('Test Number', 1)
		self.ttime = selected_experiment.get('Test Time', 30)
		self.chkcore = selected_experiment.get('Check Core', None)
		self.bucket = selected_experiment.get('Bucket', 'dummy')
		self.passstring = selected_experiment.get('Pass String', 'Test Complete')
		self.failstring = selected_experiment.get('Fail String', 'Test Failed')

		# Update labels with selected values
		self.visual_label.config(text=f"Visual: {self.visual}")
		self.content_label.config(text=f"Content: {self.content}")
		self.ttl_path_label.config(text=f"TTL Folder: {self.ttl_path}")

		# List .ttl files in the TTL Path
		self.ttl_files_listbox.delete(0, tk.END)  # Clear previous entries
		if self.ttl_path and os.path.isdir(self.ttl_path):
			ttl_files = [f for f in os.listdir(self.ttl_path) if f.endswith('.ttl')]
			for ttl_file in ttl_files:
				self.ttl_files_listbox.insert(tk.END, ttl_file)

	def start_test_thread(self):
		# Stop any existing thread
		self.stop_event.set()
		task_name = 'TTL_Check'
		if self.test_thread and self.test_thread.is_alive():
			self.test_thread.stop()
			self.test_thread.join()

		# Clear the stop event and start a new thread
		self.stop_event.clear()
		self.test_thread = ThreadHandler(target=self.run_test, name=f'Thread-{task_name}', args=())
		self.test_thread.start()

	def run_test(self, *args):
		visual = self.visual
		cmds = self.ttl_path
		ttime = self.ttime
		tnumber = self.tnumber
		bucket = self.bucket
		chkcore = self.chkcore if self.chkcore != '' else None

		try:	
			
			execute(task_name = 'TTL Test',target_func = TTL_testing, exceptions=self.exception_queue, cancel_flag = self.stop_event, args=(self.test_function, visual, cmds, chkcore, bucket, ttime, tnumber), use_process = use_process )

		except TaskCancelledException as e:
			print('TTL Test Cancelled by User')
		except Exception as e:
			print('Exception raised: ', e)  # Remove this break if you want the test to run continuously

	def reboot_unit(self):
		self.test_function.reboot_unit(waittime=60, u600w=False)

	def warm_reset(self):
		self.test_function.warm_reset(waittime=60)

	def open_edit_ttl_file(self):
		selected_index = self.ttl_files_listbox.curselection()
		if selected_index:
			selected_file = self.ttl_files_listbox.get(selected_index)
			ttl_path = self.ttl_path#_label.cget("text").replace("TTL Path: ", "")
			file_path = os.path.join(ttl_path, selected_file)
			if os.path.isfile(file_path):
				os.startfile(file_path)  # Open the file with the default text editor

	def on_close(self):
		# Stop the thread and close the window
		self.stop_event.set()
		self.top.destroy()

	def cancel_test(self):
		self.stop_event.set()
		if self.test_thread and self.test_thread.is_alive():
			self.test_thread.stop()
			self.test_thread.join()
	#def test_function(self):#self, visual, bucket, ttl_path, test='Dummy', ttime=30, tnum=1):
	#	print('add test function')
		#print(f"Running test with visual={visual}, bucket={bucket}, ttl_path={ttl_path}, test={test}, ttime={ttime}, tnum={tnum}")
		# Implement the actual test logic here

class PowerControlWindow:

	def __init__(self, parent, Framework):
		self.top = tk.Toplevel(parent)
		self.top.title("Power Control")
		self.Framework = Framework

		self.create_widgets()

	def create_widgets(self):
		tk.Button(self.top, width= 12, text=" Power ON ", command=lambda: self.control_power("on")).pack(side=tk.LEFT, padx=10, pady=5)
		tk.Button(self.top, width= 12, text=" Power OFF ", command=lambda: self.control_power("off")).pack(side=tk.LEFT, padx=10, pady=5)
		tk.Button(self.top, width= 12, text=" Power CYCLE ", command=lambda: self.control_power("cycle")).pack(side=tk.LEFT, padx=10, pady=5)

	def control_power(self, state):
		if self.Framework:
			self.Framework.power_control(state=state)
		else:
			print(f"Power control: {state}")

class MaskManagementWindow:

	def __init__(self, parent, mask_dict, update_callback, Framework=None):
		self.top = tk.Toplevel(parent)
		self.parent = parent
		self.top.title("Mask Management")
		self.mask_dict = mask_dict
		self.update_callback = update_callback
		self.Framework = Framework
		self.create_widgets()

	def create_widgets(self):
		# List to display existing masks
		self.mask_listbox = tk.Listbox(self.top)
		self.mask_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		# Populate listbox with existing masks
		for mask_name in self.mask_dict.keys():
			self.mask_listbox.insert(tk.END, mask_name)

		# Populate listbox with existing masks
		self.refresh_listbox()
	
		# Entry to set a new mask name
		self.mask_name_entry = tk.Entry(self.top, width=50)
		self.mask_name_entry.pack(fill=tk.X, padx=10, pady=5)

		# Button to open MaskEditor
		mask_editor_button = tk.Button(self.top, text="Open Mask Editor", command=self.open_mask_editor)
		mask_editor_button.pack(pady=5)

		# Button to save mask
		save_button = tk.Button(self.top, text="Save Mask", command=self.save_mask)
		save_button.pack(pady=5)

	def refresh_listbox(self):
		self.mask_listbox.delete(0, tk.END)
		for mask_name in self.mask_dict.keys():
			self.mask_listbox.insert(tk.END, mask_name)

	# Save the mask with the entered name
	def receive_masks(self, masks):
		print("New/updated masks:", masks)  # Debugging statement
		mask_name = self.mask_name_entry.get().strip()
		if mask_name:
			self.mask_dict[mask_name] = masks
			self.mask_listbox.insert(tk.END, mask_name)
			self.mask_name_entry.delete(0, tk.END)

	def open_mask_editor(self):
		# Example hex values for Compute0, Compute1, and Compute2
		idx = self.mask_listbox.curselection()
		mask_selected = self.mask_listbox.get(idx) if idx else None

		root_mask = tk.Toplevel(self.top)
		clean_mask = self.clean_mask()
		# Create an instance of SystemMaskEditor
		if self.Framework == None: 
			self.mask_dict['Default'] = clean_mask
			test_mask = clean_mask if mask_selected == None else self.mask_dict[mask_selected]
			
			compute0_core_hex = test_mask['ia_compute_0']
			compute0_cha_hex = test_mask['llc_compute_0']
			compute1_core_hex = test_mask['ia_compute_1']
			compute1_cha_hex = test_mask['llc_compute_1']
			compute2_core_hex = test_mask['ia_compute_2']
			compute2_cha_hex = test_mask['llc_compute_2']
			gme.Masking(root_mask, compute0_core_hex, compute0_cha_hex, compute1_core_hex, compute1_cha_hex, compute2_core_hex, compute2_cha_hex, product='GNR', callback = self.receive_masks)
			#masks = editor.start()
		else:
			sysmask = self.Framework.read_current_mask() #if not self.masks_var.get() else clean_mask
			
			self.Framework.Masks(basemask=sysmask, root=root_mask, callback = self.receive_masks)
		# Start the UI and get the updated masks

	def clean_mask(self):
		Full_String = "0x0000000000000000000000000000000000000000000000000000000000000000"
		masks = {	'ia_compute_0':Full_String,
		  			'ia_compute_1':Full_String,
					'ia_compute_2':Full_String,
					'llc_compute_0': Full_String,
					'llc_compute_1': Full_String,
					'llc_compute_2': Full_String,}

		return masks
	
	def save_mask(self):
		self.update_callback(self.mask_dict)
		self.top.destroy()

## Placeholder for a context manager, not being used for now
@contextmanager
def managed_thread(target, args=(), kwargs=None):
	thread = ThreadHandler(target=target, args=args, kwargs=kwargs)
	try:
		thread.start()
		yield thread
	finally:
		thread.stop()
		thread.join()

def check_exceptions(exception_queue):
	while not exception_queue.empty():
		exception = exception_queue.get()
		if isinstance(exception, TaskCancelledException):
			print("Task cancelled, stopping all executions.")
			return True
	return False

# Function to monitor execution variables -- yet to be enabled, code is not final...
def monitor_task(cancel_flag, task_name,exception_queue):

	try:
		while not cancel_flag.is_set():
			time.sleep(1)
			
		print('Cancelling now betch!!')
		
		raise TaskCancelledException(f"{task_name} cancelled")
			# Check periodically
		
	except:
		exception_queue.put(TaskCancelledException(f"{task_name} cancelled"))	
	
def monitor(cancel_flag, task_name, execution_thread):

	while execution_thread.is_alive():
		if cancel_flag.is_set():
			time.sleep(1)  # Check periodically
		if not execution_thread.is_alive():
			return 
	
	print('Cancelling now')
	execution_thread.join()
	print('Cancelling now')
	#exception_queue.put(TaskCancelledException(f"{task_name} cancelled"))
	raise TaskCancelledException(f"{task_name} cancelled")

# Offline UI Test functions 
def TestLogic(txt, cancel_flag, exception_queue):
	try:
		for i in range(10):
			if cancel_flag.is_set():
				print('Cancelling TestLogic')
				exception_queue.put(TaskCancelledException(f"{txt} logic cancelled"))
				raise TaskCancelledException(f"{txt} logic cancelled")
			print(f'Testing {txt} Logic count:{i}')
			time.sleep(1)
		print('Done')
	except TaskCancelledException as e:
		exception_queue.put(e)

def TestLogic2(txt, simulate_fail, exception_queue, cancel_flag):
	
	
	try:
		for i in range(10):
			cancel = cancel_flag.is_set() if cancel_flag != None else False
			print(f'Testing {txt} Logic count:{i} -- {cancel} :: {cancel_flag}')
			if cancel or (i == 5 and simulate_fail): 
				raise InterruptedError('SimulatedFailure')
			time.sleep(1)
		print('Done')
	except InterruptedError as e:
		print(f"Logic Interrupted by user: {e}")
		exception_queue.put(e)  # Put the exception into the queue

	except TaskCancelledException as e:
		print(f"Exception in TestLogic2: {e}")
		exception_queue.put(e)  # Put the exception into the queue

def TTL_testing(test_function, visual, cmds, chkcore, bucket, ttime, tnumber, exception_queue, cancel_flag):
	#cancel = cancel_flag.is_set() if cancel_flag != None else False
	
	try:
		cancel = True
		if test_function == None:
			print('add test function')
			for i in range(1,5):
				print(i)
				time.sleep(1)
			if i > 5 and cancel: raise InterruptedError('User SimulatedError')
			for i in range(5,10):
				print(i)
				time.sleep(1)
		
		else:
			test_function.TTL_Test(visual=visual, cmds=cmds, chkcore = chkcore, bucket = bucket, test = 'TTL_Macro_Validation', ttime=ttime, tnum=tnumber, cancel_flag=cancel_flag)
	
	except InterruptedError as e:
		print(Fore.YELLOW + f"Framework Iteration Interrupted: {e}" + Fore.WHITE)
		exception_queue.put(e)
	except TaskCancelledException as e:
		print(Fore.YELLOW + f"User Interruption in TTL_testing: {e}"+ Fore.WHITE)
		exception_queue.put(e)
	except Exception as e:
		print(Fore.RED + f"Exception in TTL_testing: {e}"+ Fore.WHITE)
		exception_queue.put(e)  # Put the exception into the queue
			
def Framework_call(Framework, data, S2TCONFIG, experiment_name, exception_queue, cancel_flag):
	try:
		# Don't access any Tkinter variables here
		# Pass primitive values only, not Tkinter variables
		
		#Framework.cancel_flag = cancel_flag
		Framework.RecipeExecutor(data=data, S2T_BOOT_CONFIG=S2TCONFIG, 
								cancel_flag=cancel_flag, experiment_name=experiment_name)

		if cancel_flag and cancel_flag.is_set():
			raise InterruptedError("Framework execution cancelled by user")
		return True
	
	except InterruptedError as e:
		print(Fore.YELLOW + f"Framework Iteration Interrupted: {e}" + Fore.WHITE)
		if exception_queue:
			exception_queue.put(e)
		return False
	except Exception as e:
		print(Fore.RED + f"Exception during Framework Execution: {e}" + Fore.WHITE)
		if exception_queue:
			exception_queue.put(e)
		return False

# Deprecated
# Executes threads or process for Framework Flow
def execute(task_name, target_func, exceptions, cancel_flag, args, use_process=True):
	handler = None
	try:
		if use_process:
			exception_queue = multiprocessing.Queue()
			handler = multiprocessing.Process(target=target_func, 
											args=args + (exception_queue, None))
		else:
			exception_queue = exceptions
			handler = ThreadHandler(target=target_func, name=f'Thread-{task_name}', 
								  args=args + (exception_queue, cancel_flag))
		
		handler.start()
		print(Fore.RED + f"Framework Control -- Starting new task: {task_name} -- " + Fore.WHITE)
		
		# Monitor execution
		#while not cancel_flag.is_set():
		#	time.sleep(0.1)
		#	if not handler.is_alive():
		#		break
		
		#if cancel_flag.is_set():
		#	if use_process and handler:
		#		handler.terminate()
		#	elif handler:
		#		handler.stop()
		#	raise TaskCancelledException(f"{task_name} cancelled by User")
		
		if handler:
			handler.join(timeout=5.0)
		
		# Check for exceptions
		try:
			if not exception_queue.empty():
				exception = exception_queue.get_nowait()
				print(f"Exception occurred during {task_name}: {exception}")
				return False
		except:
			pass
		
		return True

	except Exception as e:
		print(Fore.RED + f"Exception occurred during {task_name}: {e}" + Fore.WHITE)
		try:
			if handler:
				if use_process:
					handler.terminate()
				else:
					handler.stop()
				handler.join(timeout=2.0)
		except:
			pass
		
		if exceptions:
			try:
				exceptions.put(e)
			except:
				pass
		return False
	
def OpenExperiment(path):
	# Placeholder for the actual implementation
	# Assume fh.process_excel_file and fh.create_tabulated_format are defined elsewhere

	if path.endswith('.json'):
		data_from_sheets = fh.load_json_file(path)
		#tabulated_df = data_from_sheets
	elif path.endswith('.xlsx'):
		data_from_sheets = fh.process_excel_file(path)
		# Create the tabulated format
	else: return None

	return data_from_sheets

def Convert_xlsx_to_json(file_path, experiments):
	data_from_json = fh.save_excel_to_json(file_path, experiments)
	return data_from_json

def run(Framework):
	try:
		root = tk.Tk()
		
		# Ensure we're in the main thread
		if threading.current_thread() != threading.main_thread():
			raise RuntimeError("GUI must be started from main thread")
		
		app = DebugFrameworkControlPanel(root, Framework)
		root.mainloop()
		
	except Exception as e:
		print(f"Error starting GUI: {e}")
	finally:
		# Ensure cleanup
		try:
			root.quit()
			root.destroy()
		except:
			pass

def run_process(Framework):

	# Enable multiprocessing support
	multiprocessing.set_start_method('spawn', force=True)  # Important for Windows
	
	root = tk.Tk()
	app = DebugFrameworkControlPanel(root, Framework=Framework)  # Framework will run in process
	root.mainloop()

if __name__ == "__main__":
	multiprocessing.set_start_method('spawn', force=True)  # Important for Windows
	Framework = None
	root = tk.Tk()
	app = DebugFrameworkControlPanel(root, Framework)
	root.mainloop()
