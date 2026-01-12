# Create EnhancedThreadSafeState.py

import threading
import time
import sys
import os

from datetime import datetime
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Set, Callable
from dataclasses import dataclass, field

''' Framework Threads Handler -- rev 1.7'''

current_dir= os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

from ExecutionHandler.utils.DebugLogger import (
	debug_log, 
	is_debug_enabled,
	)

debug_enabled = True

class ExecutionCommand(Enum):
	"""Enumeration of all possible execution commands"""
	# Core execution commands
	CANCEL = auto()
	END_EXPERIMENT = auto()
	PAUSE = auto()
	RESUME = auto()
	
	# Step-by-step commands
	STEP_CONTINUE = auto()
	ENABLE_STEP_MODE = auto()
	DISABLE_STEP_MODE = auto()
	
	# Advanced commands
	SKIP_CURRENT_TEST = auto()
	RETRY_CURRENT_TEST = auto()
	CHANGE_LOG_LEVEL = auto()
	EMERGENCY_STOP = auto()
	
	# Status commands
	REQUEST_STATUS = auto()
	HEARTBEAT = auto()

@dataclass
class CommandData:
	"""Data structure for command with metadata"""
	command: ExecutionCommand
	timestamp: float = field(default_factory=time.time)
	data: Optional[Dict[str, Any]] = None
	processed: bool = False
	response: Optional[Any] = None  # For command responses
	acknowledged: bool = False  # NEW: Track if acknowledged
	processing_started: bool = False  # NEW: Track if processing started

	def __post_init__(self):
		if self.data is None:
			self.data = {}

class EnhancedThreadSafeState:
	"""Enhanced thread-safe state manager with command system"""
	
	def __init__(self):
		self._lock = threading.RLock()
		self.debug_enabled = debug_enabled
		# Core execution state
		self._state: Dict[str, Any] = {
			'execution_active': False,
			'current_experiment': None,
			'current_iteration': 0,
			'total_iterations': 0,
			'step_mode_enabled': False,
			'log_level': 'INFO',
			'waiting_for_step': False,
			'framework_ready': True
		}
		
		# Command tracking
		self._active_commands: Set[ExecutionCommand] = set()
		self._command_history: list[CommandData] = []
		self._max_history = 100
		
		# Command data storage
		self._command_data: Dict[ExecutionCommand, Any] = {}
		
		# Status tracking
		self._last_heartbeat = time.time()
		
		# Command response callbacks
		self._response_callbacks: Dict[ExecutionCommand, Callable] = {}

		# DEBUG: Command lifecycle tracking
		self._command_lifecycle: Dict[ExecutionCommand, Dict[str, float]] = {}

		# NEW: Persistent command state for thread synchronization
		self._persistent_command_state: Dict[ExecutionCommand, Dict[str, Any]] = {}
		self._persistent_state_lock = threading.RLock()
		self._persistent_state_timeout = 10.0  # 10 seconds timeout

		# Code Debugger Log
		debug_log("EnhancedThreadSafeState initialized", 1, "THREAD_STATE_INIT")
	
	# ==================== DEBUG MANAGEMENT ====================

	def _debug_log(self, message: str, level: int = 1, category: str = "THREAD_STATE"):
		"""Debug logging with thread info"""

		# Checks global and internal flag
		if is_debug_enabled() and self.debug_enabled:
			try:
				safe_message = message.encode('ascii', 'ignore').decode('ascii')
				thread_name = threading.current_thread().name
				debug_log(f"THREAD_HANDLER: [{thread_name}][{level}] - {safe_message}", level, category)
			except Exception as e:
				debug_log(f'Error with debug:{e}',3,'THREAD_DEBUG')

	def _debug_breakpoint(self, breakpoint_name: str, command: ExecutionCommand = None, extra_data: Dict = None):
		"""Debug breakpoint with detailed state information"""
		if not is_debug_enabled() or not self.debug_enabled:
			return

		try:    
			thread_name = threading.current_thread().name
			timestamp = time.strftime("%H:%M:%S")
			
			self._debug_log(f"{'='*60}", 1, "DEBUG_BREAKPOINT")
			self._debug_log(f"DEBUG BREAKPOINT: {breakpoint_name}", 1, "DEBUG_BREAKPOINT")
			self._debug_log(f"Time: {timestamp}", 1, "DEBUG_BREAKPOINT")
			self._debug_log(f"Thread: {thread_name}", 1, "DEBUG_BREAKPOINT")
			
			if command:
				self._debug_log(f"Command: {command.name}", 1, "DEBUG_BREAKPOINT")
				
				# Command lifecycle info
				if command in self._command_lifecycle:
					lifecycle = self._command_lifecycle[command]
					self._debug_log("Command Lifecycle:", 1, "DEBUG_BREAKPOINT")
					for event, event_time in lifecycle.items():
						event_timestamp = time.strftime("%H:%M:%S")
						self._debug_log(f"  {event}: {event_timestamp}", 1, "DEBUG_BREAKPOINT")
			
			with self._lock:
				self._debug_log(f"Active Commands: {[cmd.name for cmd in self._active_commands]}", 1, "DEBUG_BREAKPOINT")
				self._debug_log(f"Execution Active: {self._state.get('execution_active', False)}", 1, "DEBUG_BREAKPOINT")
				self._debug_log(f"Current Experiment: {self._state.get('current_experiment', 'None')}", 1, "DEBUG_BREAKPOINT")
				self._debug_log(f"Current Iteration: {self._state.get('current_iteration', 0)}", 1, "DEBUG_BREAKPOINT")
				
				# Recent command history
				recent_commands = self._command_history[-3:] if self._command_history else []
				self._debug_log("Recent Commands:", 1, "DEBUG_BREAKPOINT")
				for cmd_data in recent_commands:
					status = " Acked" if cmd_data.acknowledged else (" Processing" if cmd_data.processing_started else " Pending")
					self._debug_log(f"  {cmd_data.command.name}: {status}", 1, "DEBUG_BREAKPOINT")
			
			if extra_data:
				self._debug_log(f"Extra Data: {extra_data}", 1, "DEBUG_BREAKPOINT")
				
			self._debug_log(f"{'='*60}", 1, "DEBUG_BREAKPOINT")
		except Exception as e:
			self._debug_log(f'Error with debug breakpoint: {e}', 3, "DEBUG_ERROR")

	# ==================== INIT MANAGEMENT ====================

	def prepare_for_execution(self) -> bool:
		"""Prepare state for new execution"""
		self._debug_log("=== PREPARING FOR EXECUTION ===", 1, "EXECUTION_PREP")
		self._debug_breakpoint("PREPARE_FOR_EXECUTION_START")
		try:
			with self._lock:
				self._debug_log(f"Before clearing - Active commands: {[cmd.name for cmd in self._active_commands]}", 1, "COMMAND_CLEAR")
				self._debug_log(f"Before clearing - Command data keys: {list(self._command_data.keys())}", 1, "COMMAND_CLEAR")
		
				commands_to_clear = self._active_commands.copy()
				self._debug_log(f"Clearing {len(commands_to_clear)} commands: {[cmd.name for cmd in commands_to_clear]}", 1, "COMMAND_CLEAR")
				
				# Clear commands but preserve execution state if already set
				preserve_execution_state = self._state.get('execution_active', False)
				current_experiment = self._state.get('current_experiment')
				total_iterations = self._state.get('total_iterations', 0)
				
				self._debug_log(f"Preserve execution state: {preserve_execution_state}", 1, "STATE_PRESERVE")
				
				# Clear active commands completely
				self._active_commands.clear()
				
				# Clear all command data
				self._command_data.clear()
				
				# Clear response callbacks
				self._response_callbacks.clear()
				
				# Mark all unprocessed commands in history as processed/cancelled
				unprocessed_count = 0
				for cmd_data in self._command_history:
					if not cmd_data.processed:
						cmd_data.processed = True
						cmd_data.response = "Cleared during preparation"
						cmd_data.acknowledged = True
						unprocessed_count += 1

				self._debug_log(f"Marked {unprocessed_count} unprocessed commands as cleared", 1, "COMMAND_CLEAR")

				# [ DONE ] Only reset execution state if not already active
				if not preserve_execution_state:
					self._debug_log("Resetting execution state to inactive", 1, "STATE_RESET")
					self._state.update({
						'execution_active': False,
						'current_experiment': None,
						'current_iteration': 0,
						'total_iterations': 0,
						'waiting_for_step': False,
						'framework_ready': True
					})
				else:
					# Preserve active execution state
					self._debug_log("Preserving active execution state", 1, "STATE_PRESERVE")
					self._state.update({
						'execution_active': True,
						'current_experiment': current_experiment,
						'total_iterations': total_iterations,
						'waiting_for_step': False,
						'framework_ready': True
					})
				
				# Update heartbeat
				self._last_heartbeat = time.time()
				self._debug_log("Heartbeat updated", 1, "HEARTBEAT")

				self._debug_breakpoint("PREPARE_FOR_EXECUTION_COMPLETE")
				self._debug_log("=== EXECUTION PREPARATION COMPLETED ===", 1, "EXECUTION_PREP")
				
				return True
				
		except Exception as e:
			self._debug_log(f"Error preparing for execution: {e}", 3, "EXECUTION_PREP_ERROR")
			print(f"Error preparing for execution: {e}")
			return False
	
	def finalize_execution(self, reason: str = "completed"):
		"""Finalize execution and cleanup"""
		self._debug_log(f"=== FINALIZING EXECUTION: {reason} ===", 1, "EXECUTION_FINALIZE")
		try:
			with self._lock:
				self._debug_log("Marking execution as inactive", 1, "STATE_UPDATE")
				# Mark as inactive
				self._state['execution_active'] = False
				self._state['framework_ready'] = True
				
				# Clear execution-specific commands
				execution_commands = {
					ExecutionCommand.CANCEL,
					ExecutionCommand.END_EXPERIMENT,
					ExecutionCommand.PAUSE,
					ExecutionCommand.RESUME,
					ExecutionCommand.STEP_CONTINUE,
					ExecutionCommand.EMERGENCY_STOP
				}
				
				cleared_commands = []
				for cmd in execution_commands:
					if cmd in self._active_commands:
						cleared_commands.append(cmd.name)
						self._active_commands.discard(cmd)
						self._command_data.pop(cmd, None)
				
				self._debug_log(f"Cleared execution commands: {cleared_commands}", 1, "COMMAND_CLEAR")

				# Add finalization to history
				self._command_history.append(CommandData(
					command=ExecutionCommand.REQUEST_STATUS,  # Use as generic status command
					data={"action": "finalize", "reason": reason},
					processed=True
				))
				
				self._trim_history()
				self._debug_log(f"Execution finalized successfully: {reason}", 1, "EXECUTION_FINALIZE")
		
		except Exception as e:
			self._debug_log(f"Error finalizing execution: {e}", 3, "FINALIZE_ERROR")
			print(f"Error finalizing execution: {e}")
	
	def is_ready_for_execution(self) -> bool:
		"""Check if state is ready for new execution"""
		with self._lock:
			ready =  (self._state.get('framework_ready', True) and 
					not self._state.get('execution_active', False) and
					not self.has_command(ExecutionCommand.EMERGENCY_STOP))

			self._debug_log(f"Ready for execution check: {ready}", 1, "READINESS_CHECK")
			self._debug_log(f"  framework_ready: {self._state.get('framework_ready', True)}", 1, "READINESS_CHECK")
			self._debug_log(f"  execution_active: {self._state.get('execution_active', False)}", 1, "READINESS_CHECK")
			self._debug_log(f"  emergency_stop: {self.has_command(ExecutionCommand.EMERGENCY_STOP)}", 1, "READINESS_CHECK")

			return ready
				
	# ==================== COMMAND MANAGEMENT ====================
	
	def issue_command(self, command: ExecutionCommand, data: Optional[Dict[str, Any]] = None, 
					 callback: Optional[Callable] = None) -> bool:
		"""Issue a command (called from main thread)"""
		self._debug_log(f"=== ISSUING COMMAND: {command.name} ===", 1, "COMMAND_ISSUE")

		# [CHECK] Special debug tracing for critical commands
		if command in [ExecutionCommand.CANCEL, ExecutionCommand.END_EXPERIMENT]:
			import traceback
			thread_name = threading.current_thread().name
			timestamp = datetime.now().strftime("%H:%M:%S.%")[:-3]
			
			self._debug_log(f"CRITICAL COMMAND ISSUED: {command.name}", 2, "CRITICAL_COMMAND")
			self._debug_log(f"  Thread: {thread_name}", 2, "CRITICAL_COMMAND")
			self._debug_log(f"  Timestamp: {timestamp}", 2, "CRITICAL_COMMAND")
			self._debug_log(f"  Data: {data}", 2, "CRITICAL_COMMAND")
			self._debug_log(f"  Callback: {callback is not None}", 2, "CRITICAL_COMMAND")
			
			# Show detailed stack trace for these critical commands
			stack = traceback.format_stack()
			self._debug_log(f"Stack trace for {command.name} command:", 2, "CRITICAL_COMMAND")
			for i, line in enumerate(stack[-8:]):  # Show more frames for critical commands
				if 'ThreadsHandler.py' not in line:  # Skip our own debug code
					self._debug_log(f"     [{i}] {line.strip()}")
		
		self._debug_breakpoint("COMMAND_ISSUE_START", command, {"data": data})
		
		try:
			with self._lock:
				# Initialize command lifecycle tracking
				self._command_lifecycle[command] = {
					'issued': time.time()
				}
				
				self._debug_log(f"Command lifecycle tracking initialized for {command.name}", 1, "LIFECYCLE")
				
				# Prevent duplicate commands for certain types
				if command in [ExecutionCommand.CANCEL, ExecutionCommand.END_EXPERIMENT, ExecutionCommand.EMERGENCY_STOP]:
					if command in self._active_commands:
						self._debug_log(f"Command {command.name} already active - skipping duplicate", 2, "DUPLICATE_COMMAND")
						return True  # Already active
				
				command_data = CommandData(command=command, data=data or {})
				
				# Add to active commands
				self._active_commands.add(command)
				self._debug_log(f"Command {command.name} added to active commands", 1, "COMMAND_ACTIVE")
				
				# Store command data if provided
				if data:
					self._command_data[command] = data
					self._debug_log(f"Command data stored for {command.name}: {data}", 1, "COMMAND_DATA")

				# NEW: Set persistent success state for critical commands
				if command in [ExecutionCommand.STEP_CONTINUE, ExecutionCommand.END_EXPERIMENT, 
							 ExecutionCommand.CANCEL, ExecutionCommand.PAUSE, ExecutionCommand.RESUME]:
					self._debug_log(f"Setting persistent success state for {command.name}", 1, "PERSISTENT_STATE")
					
					self.set_persistent_command_state(
						command, 
						'success', 
						data,
						timeout=5.0  # 5 second timeout for these critical commands
					)

				# Store callback if provided
				if callback:
					self._response_callbacks[command] = callback
					self._debug_log(f"Callback registered for {command.name}", 1, "COMMAND_CALLBACK")
				
				# Add to history
				self._command_history.append(command_data)
				self._trim_history()
				
				# Handle immediate state changes for certain commands
				self._debug_log(f"Processing immediate state changes for {command.name}", 1, "IMMEDIATE_PROCESS")
				self._process_immediate_commands(command, data or {})

				self._debug_breakpoint("COMMAND_ISSUE_COMPLETE", command, {
					"active_commands_count": len(self._active_commands),
					"command_in_active": command in self._active_commands
				})

				self._debug_log(f"Command {command.name} issued successfully", 1, "COMMAND_ISSUE")
				return True
				
		except Exception as e:
			self._debug_log(f"Error issuing command {command}: {e}", 3, "COMMAND_ISSUE_ERROR")
			print(f"Error issuing command {command}: {e}")
			return False

	def has_command(self, command: ExecutionCommand) -> bool:
		"""Check if a specific command is active"""
		with self._lock:
			has_cmd = command in self._active_commands
			
			# Find command data for more info
			cmd_data = None
			for cmd in reversed(self._command_history):
				if cmd.command == command:
					cmd_data = cmd
					break
						
			self._debug_log(f"Command check {command.name}: {'ACTIVE' if has_cmd else 'INACTIVE'}" + 
								(f" (Acked: {cmd_data.acknowledged}, Processing: {cmd_data.processing_started})" if cmd_data else ""), 
								1, "COMMAND_CHECK")			
			return has_cmd

	def start_processing_command(self, command: ExecutionCommand) -> bool:
		"""Mark command as processing started (called when background thread starts handling it)"""
		self._debug_log(f"=== STARTING COMMAND PROCESSING: {command.name} ===", 1, "COMMAND_PROCESSING")
		self._debug_breakpoint("COMMAND_PROCESSING_START", command)
		
		try:
			with self._lock:
				if command not in self._active_commands:
					self._debug_log(f"Cannot start processing {command.name} - not in active commands", 3, "PROCESSING_ERROR")
					return False
				
				# Update lifecycle
				if command in self._command_lifecycle:
					self._command_lifecycle[command]['processing_started'] = time.time()
					self._debug_log(f"Processing start time recorded for {command.name}", 1, "LIFECYCLE")
				
				# Mark in history
				for cmd_data in reversed(self._command_history):
					if cmd_data.command == command and not cmd_data.processing_started:
						cmd_data.processing_started = True
						self._debug_log(f"Command history updated - processing started for {command.name}", 1, "HISTORY_UPDATE")
						break
				
				self._debug_log(f"Started processing command {command.name}", 1, "COMMAND_PROCESSING")
				return True
				
		except Exception as e:
			self._debug_log(f"Error starting processing for {command}: {e}", 3, "PROCESSING_ERROR")
			return False

	def get_active_commands(self) -> Set[ExecutionCommand]:
		"""Get all active commands"""
		
		with self._lock:
			active_cmds = self._active_commands.copy()
			self._debug_log(f"Active commands requested: {[cmd.name for cmd in active_cmds]}", 1, "ACTIVE_COMMANDS")
			return active_cmds
	
	def acknowledge_command(self, command: ExecutionCommand, response: Any = None) -> bool:
		"""Acknowledge that a command has been processed (called from background thread)"""
		self._debug_log(f"=== ACKNOWLEDGING COMMAND: {command.name} ===", 1, "COMMAND_ACK")
		self._debug_breakpoint("COMMAND_ACKNOWLEDGE_START", command, {"response": response})
		
		try:
			with self._lock:

				if command not in self._active_commands:
					self._debug_log(f"Cannot acknowledge {command.name} - not in active commands", 2, "ACK_WARNING")
					return False
				
				if command in self._command_lifecycle:
					self._command_lifecycle[command]['acknowledged'] = time.time()
					self._debug_log(f"Acknowledgment time recorded for {command.name}", 1, "LIFECYCLE")
				
				self._active_commands.remove(command)
					
				# Mark as processed in history
				for cmd_data in reversed(self._command_history):
					if cmd_data.command == command and not cmd_data.processed:
						cmd_data.processed = True
						cmd_data.response = response
						cmd_data.acknowledged = True
						self._debug_log(f"Command history updated - acknowledged for {command.name}", 1, "HISTORY_UPDATE")
						break
					
				# Execute callback if exists
				callback = self._response_callbacks.pop(command, None)
				if callback:
					try:
						self._debug_log(f"Executing callback for {command.name}", 1, "CALLBACK")
						callback(response)
					except Exception as e:
						self._debug_log(f"Callback error for {command}: {e}", 3, "CALLBACK_ERROR")
						print(f"Callback error for {command}: {e}")
					
				# Clean up command data
				self._debug_log(f"Command data cleaned up for {command.name}", 1, "CLEANUP")	
				self._command_data.pop(command, None)
				self._debug_log(f"Command {command.name} acknowledged successfully", 1, "COMMAND_ACK")

				return True
			
				
		except Exception as e:
			self._debug_log(f"Error acknowledging command {command}: {e}", 3, "ACK_ERROR")
			print(f"Error acknowledging command {command}: {e}")
			return False
	
	def get_command_data(self, command: ExecutionCommand) -> Optional[Dict[str, Any]]:
		"""Get data associated with a command"""
		with self._lock:
			data = self._command_data.get(command, {}).copy()
			self._debug_log(f"Command data requested for {command.name}: {bool(data)}", 1, "COMMAND_DATA")
			return data
	
	def clear_all_commands(self):
		"""Clear all active commands"""
		self._debug_log("=== CLEARING ALL COMMANDS ===", 1, "COMMAND_CLEAR")
		with self._lock:
			cleared_commands = [cmd.name for cmd in self._active_commands]
			self._active_commands.clear()
			self._command_data.clear()
			self._debug_log(f"Cleared commands: {cleared_commands}", 1, "COMMAND_CLEAR")
	   
	# ==================== PERSISTENT COMMAND STATE METHODS ====================
	
	def set_persistent_command_state(self, command: ExecutionCommand, state: str, 
								   data: Dict[str, Any] = None, timeout: float = None):
		"""Set persistent command state that survives across thread boundaries"""
		self._debug_log(f"=== SETTING PERSISTENT STATE: {command.name} = {state} ===", 1, "PERSISTENT_STATE")

		with self._persistent_state_lock:
			timeout_time = time.time() + (timeout or self._persistent_state_timeout)
			
			self._persistent_command_state[command] = {
				'state': state,
				'data': data or {},
				'timestamp': time.time(),
				'timeout': timeout_time,
				'thread_id': threading.current_thread().ident,
				'thread_name': threading.current_thread().name
			}
			
			self._debug_log(f"Persistent state set for {command.name}: {state} (timeout in {timeout or self._persistent_state_timeout}s)", 1, "PERSISTENT_STATE")
	
	def get_persistent_command_state(self, command: ExecutionCommand, 
								   clear_after_read: bool = False) -> Dict[str, Any]:
		"""Get persistent command state"""
		with self._persistent_state_lock:
			# Clean up expired states first
			self._cleanup_expired_persistent_states()
			
			if command not in self._persistent_command_state:
				self._debug_log(f"No persistent state found for {command.name}", 1, "PERSISTENT_STATE")
				return {'state': None, 'found': False}
			
			state_info = self._persistent_command_state[command].copy()
			state_info['found'] = True
			
			self._debug_log(f"Persistent state retrieved for {command.name}: {state_info['state']}", 1, "PERSISTENT_STATE")

			if clear_after_read:
				del self._persistent_command_state[command]
				self._debug_log(f"Persistent state cleared after read for {command.name}", 1, "PERSISTENT_STATE")
			
			return state_info
	
	def clear_persistent_command_state(self, command: ExecutionCommand):
		"""Clear specific persistent command state"""
		self._debug_log(f"Manually clearing persistent state for {command.name}", 1, "PERSISTENT_STATE")
		with self._persistent_state_lock:
			if command in self._persistent_command_state:
				del self._persistent_command_state[command]
				self._debug_log(f"Persistent state manually cleared for {command.name}", 1, "PERSISTENT_STATE")
	
	def _cleanup_expired_persistent_states(self):
		"""Clean up expired persistent states"""
		current_time = time.time()
		expired_commands = []
		
		for command, state_info in self._persistent_command_state.items():
			if current_time > state_info['timeout']:
				expired_commands.append(command)
		
		for command in expired_commands:
			del self._persistent_command_state[command]
			self._debug_log(f"Expired persistent state cleaned up for {command.name}", 1, "PERSISTENT_CLEANUP")
	
	def has_persistent_success_state(self, command: ExecutionCommand) -> bool:
		"""Check if command has a persistent success state"""
		state_info = self.get_persistent_command_state(command)
		has_success = state_info['found'] and state_info.get('state') == 'success'
		self._debug_log(f"Persistent success state check for {command.name}: {has_success}", 1, "PERSISTENT_STATE")
		return has_success
		
	# ==================== CONVENIENCE COMMAND METHODS ====================
	
	def cancel(self, reason: str = "User requested", callback: Optional[Callable] = None) -> bool:
		"""Issue cancel command"""
		#return self.issue_command(ExecutionCommand.CANCEL, {"reason": reason}, callback)
		"""Issue cancel command with debug"""
		self._debug_log(f"Issuing CANCEL command: {reason}", 1, "CANCEL_COMMAND")
		return self.issue_command(ExecutionCommand.CANCEL, {"reason": reason}, callback)
		
	def end_experiment(self, reason: str = "User requested", callback: Optional[Callable] = None) -> bool:
		"""Issue end experiment command"""
		#return self.issue_command(ExecutionCommand.END_EXPERIMENT, {"reason": reason}, callback)
		"""Issue end experiment command with debug"""
		self._debug_log(f"Issuing END_EXPERIMENT command: {reason}", 1, "END_COMMAND")
		return self.issue_command(ExecutionCommand.END_EXPERIMENT, {"reason": reason}, callback)

	def pause(self, reason: str = "User requested", callback: Optional[Callable] = None) -> bool:
		"""Issue pause command"""
		self._debug_log(f"Issuing PAUSE command: {reason}", 1, "PAUSE_COMMAND")
		return self.issue_command(ExecutionCommand.PAUSE, {"reason": reason}, callback)
	
	def resume(self, reason: str = "User requested", callback: Optional[Callable] = None) -> bool:
		"""Issue resume command"""
		self._debug_log(f"Issuing RESUME command: {reason}", 1, "RESUME_COMMAND")
		return self.issue_command(ExecutionCommand.RESUME, {"reason": reason}, callback)
	
	def step_continue(self, callback: Optional[Callable] = None) -> bool:

		self._debug_log("=== STEP CONTINUE REQUESTED ===", 1, "STEP_CONTINUE")
		
		# Get current state for debugging
		with self._lock:
			exec_active = self._state.get('execution_active', False)
			step_mode = self._state.get('step_mode_enabled', False)
			waiting = self._state.get('waiting_for_step', False)
			
			self._debug_log("Step continue state check:", 1, "STEP_CONTINUE")
			self._debug_log(f"  execution_active: {exec_active}", 1, "STEP_CONTINUE")
			self._debug_log(f"  step_mode_enabled: {step_mode}", 1, "STEP_CONTINUE")
			self._debug_log(f"  waiting_for_step: {waiting}", 1, "STEP_CONTINUE")
	  	
		# Validate state before issuing command
		if not self._state.get('execution_active', False):
			self._debug_log("WARNING: Step continue when execution not active", 2, "STEP_CONTINUE_WARNING")
			print("WARNING: Attempting step continue when execution not active")
			#return False
		
		if not self._state.get('step_mode_enabled', False):
			self._debug_log("WARNING: Step continue when step mode not enabled", 2, "STEP_CONTINUE_WARNING")
			print("WARNING: Attempting step continue when step mode not enabled")
			#return False
		
		if not self._state.get('waiting_for_step', False):
			self._debug_log("WARNING: Step continue when not waiting for step", 2, "STEP_CONTINUE_WARNING")
			print("WARNING: Attempting step continue when not waiting for step")
			#return False

		# ALWAYS issue the command (no validation)
		self._debug_log("Issuing STEP_CONTINUE command (validation warnings only)", 1, "STEP_CONTINUE")
		success = self.issue_command(ExecutionCommand.STEP_CONTINUE, {}, callback)
		
		if success:
			self._debug_log("STEP_CONTINUE command issued successfully", 1, "STEP_CONTINUE")
		else:
			self._debug_log("STEP_CONTINUE command FAILED to issue", 3, "STEP_CONTINUE_ERROR")

					
		"""Issue step continue command"""
		return success
	
	def enable_step_mode(self) -> bool:
		"""Enable step-by-step mode"""
		self._debug_log("Enabling step-by-step mode", 1, "STEP_MODE")
		return self.issue_command(ExecutionCommand.ENABLE_STEP_MODE)
	
	def disable_step_mode(self) -> bool:
		"""Disable step-by-step mode"""
		self._debug_log("Disabling step-by-step mode", 1, "STEP_MODE")
		return self.issue_command(ExecutionCommand.DISABLE_STEP_MODE)
	
	def emergency_stop(self, reason: str = "Emergency stop requested") -> bool:
		"""Issue emergency stop command"""
		self._debug_log(f"Issuing EMERGENCY_STOP command: {reason}", 3, "EMERGENCY_STOP")
		return self.issue_command(ExecutionCommand.EMERGENCY_STOP, {"reason": reason})
	
	def skip_current_test(self, reason: str = "User requested skip") -> bool:
		"""Skip current test"""
		self._debug_log(f"Issuing SKIP_CURRENT_TEST command: {reason}", 1, "SKIP_TEST")
		return self.issue_command(ExecutionCommand.SKIP_CURRENT_TEST, {"reason": reason})
	
	def change_log_level(self, level: str) -> bool:
		"""Change logging level"""
		self._debug_log(f"Changing log level to: {level}", 1, "LOG_LEVEL")
		return self.issue_command(ExecutionCommand.CHANGE_LOG_LEVEL, {"level": level})
	
	# ==================== STATE CHECKING METHODS ====================
	
	def is_cancelled(self) -> bool:
		"""Check if cancellation was requested"""
		#return self.has_command(ExecutionCommand.CANCEL) or self.has_command(ExecutionCommand.EMERGENCY_STOP)
		"""Check if cancellation was requested with debug info"""
		with self._lock:
			cancel_active = ExecutionCommand.CANCEL in self._active_commands
			emergency_active = ExecutionCommand.EMERGENCY_STOP in self._active_commands
			result = cancel_active or emergency_active
			
			if result:
				self._debug_log(f"Cancellation check: TRUE (Cancel: {cancel_active}, Emergency: {emergency_active})", 1, "CANCELLATION_CHECK")
			
			return result
		   
	def is_ended(self) -> bool:
		"""Check if end was requested"""
		#return self.has_command(ExecutionCommand.END_EXPERIMENT)
		"""Check if end was requested with debug info"""
		with self._lock:
			result = ExecutionCommand.END_EXPERIMENT in self._active_commands
			
			if result:
				self._debug_log("End experiment check: TRUE", 1, "END_CHECK")
			
			return result
		   
	def is_paused(self) -> bool:
		"""Check if pause was requested"""
		#return self.has_command(ExecutionCommand.PAUSE) and not self.has_command(ExecutionCommand.RESUME)
		"""Check if pause was requested with debug info"""
		with self._lock:
			pause_active = ExecutionCommand.PAUSE in self._active_commands
			resume_active = ExecutionCommand.RESUME in self._active_commands
			result = pause_active and not resume_active
			
			if pause_active or resume_active:
				self._debug_log(f"Pause check: {result} (Pause: {pause_active}, Resume: {resume_active})", 1, "PAUSE_CHECK")
			
			return result
		   
	def should_stop(self) -> bool:
		"""Check if execution should stop completely with debug info"""
		with self._lock:
			cancel = ExecutionCommand.CANCEL in self._active_commands
			end = ExecutionCommand.END_EXPERIMENT in self._active_commands
			emergency = ExecutionCommand.EMERGENCY_STOP in self._active_commands

			is_step_mode = self.get_state('step_mode_enabled', False) 
			end_normal = end and not is_step_mode
			
			result = cancel or emergency # End is not going to stop in step mode -- cancel or end or emergency
			
			if result:
				self._debug_log(f"Should stop: TRUE (Cancel: {cancel}, End: {end}, Emergency: {emergency})", 1, "SHOULD_STOP")
				self._debug_log(f"Step mode enabled: {is_step_mode}", 1, "SHOULD_STOP")
				self._debug_log(f"Active commands: {[cmd.name for cmd in self._active_commands]}", 1, "SHOULD_STOP")
			
			return result
			
	def should_step_continue(self) -> bool:
		"""Check if step continue was requested"""
		result = self.has_command(ExecutionCommand.STEP_CONTINUE)
		if result:
			self._debug_log("Step continue command detected", 1, "STEP_CONTINUE_CHECK")
		return result
		
	def is_step_mode_enabled(self) -> bool:
		"""Check if step mode is enabled"""
		with self._lock:
			result = self._state.get('step_mode_enabled', False)
			self._debug_log(f"Step mode enabled check: {result}", 1, "STEP_MODE_CHECK")
			return result
		
	# ==================== STATE MANAGEMENT ====================
	
	def set_state(self, key: str, value: Any):
		"""Set a state value"""
		with self._lock:
			old_value = self._state.get(key)
			
			if key == 'execution_active':
				import traceback
				thread_name = threading.current_thread().name
				timestamp = datetime.now().strftime("%H:%M:%S.%")[:-3]
				
				if old_value != value:
					self._debug_log(f"EXECUTION_ACTIVE CHANGE: {old_value} -> {value} (Thread: {thread_name}) at {timestamp}", 2, "EXECUTION_STATE")
					
					# Print detailed stack trace
					stack = traceback.format_stack()
					self._debug_log("Stack trace for execution_active change:", 2, "EXECUTION_STATE")
					for i, line in enumerate(stack[-8:]):  # Show more frames
						self._debug_log(f"  [{i}] {line.strip()}", 2, "EXECUTION_STATE")
					
					if value == False:
						self._debug_log("CRITICAL: execution_active set to FALSE - this will break step mode!", 3, "EXECUTION_STATE")
				else:
					# Even if value is the same, log it for debugging
					self._debug_log(f"execution_active set to same value: {value} (Thread: {thread_name})", 1, "EXECUTION_STATE")
			elif key in ['step_mode_enabled', 'waiting_for_step', 'current_iteration']:
				# Log other important state changes
				if old_value != value:
					debug_log(f"State change - {key}: {old_value} -> {value}", 1, "STATE_CHANGE")			
									
			self._state[key] = value
	
	def get_state(self, key: str, default: Any = None) -> Any:
		"""Get a state value"""
		with self._lock:
			value = self._state.get(key, default)
			# Only log for critical state keys to avoid spam
			if key in ['execution_active', 'step_mode_enabled', 'waiting_for_step']:
				debug_log(f"State get - {key}: {value}", 1, "STATE_GET")
			return value
		
	def update_state(self, **kwargs):
		"""Update multiple state values with race condition debugging"""
		self._debug_log(f"=== UPDATING STATE: {list(kwargs.keys())} ===", 1, "STATE_UPDATE")

		with self._lock:
			if 'execution_active' in kwargs:
				old_value = self._state.get('execution_active')
				new_value = kwargs['execution_active']
				
				import traceback
				thread_name = threading.current_thread().name
				timestamp = datetime.now().strftime("%H:%M:%S.%")[:-3]
				
				self._debug_log(f"EXECUTION_ACTIVE UPDATE START: {old_value} -> {new_value} (Thread: {thread_name}) at {timestamp}", 2, "EXECUTION_STATE")
				
				# [ DONE ] Actually update the state
				self._state.update(kwargs)
				
				# [ DONE ] Immediately verify the update worked
				actual_value = self._state.get('execution_active')
				if actual_value != new_value:
					self._debug_log(f"CRITICAL BUG: State update failed! Expected {new_value}, got {actual_value}", 3, "STATE_UPDATE_ERROR")
				else:
					self._debug_log(f"State update successful: execution_active = {actual_value}", 1, "STATE_UPDATE")
				
				if old_value != new_value:
					stack = traceback.format_stack()
					self._debug_log("Stack trace for execution_active update:", 2, "EXECUTION_STATE")
					for i, line in enumerate(stack[-6:]):
						self._debug_log(f"  [{i}] {line.strip()}")
					
					if new_value == False:
						self._debug_log("CRITICAL: execution_active updated to FALSE!", 3, "EXECUTION_STATE")
			else:
				# Normal update for non-execution_active keys
				self._debug_log(f"Updating state keys: {list(kwargs.keys())}", 1, "STATE_UPDATE")
				self._state.update(kwargs)

	def get_full_state(self) -> Dict[str, Any]:
		"""Get complete state snapshot"""
		with self._lock:
			state_snapshot = {
				'state': self._state.copy(),
				'active_commands': list(self._active_commands),
				'last_heartbeat': self._last_heartbeat,
				'command_count': len(self._command_history)
			}
			self._debug_log(f"Full state snapshot requested: {len(state_snapshot['active_commands'])} active commands", 1, "STATE_SNAPSHOT")
			return state_snapshot
	
	def reset(self):
		"""Reset all state and commands"""
		self._debug_log("=== RESETTING ALL STATE AND COMMANDS ===", 1, "RESET")

		with self._lock:
			self._state = {
				'execution_active': False,
				'current_experiment': None,
				'current_iteration': 0,
				'total_iterations': 0,
				'step_mode_enabled': False,
				'log_level': 'INFO'
			}
			self._active_commands.clear()
			self._command_data.clear()
			self._command_history.clear()
			self._last_heartbeat = time.time()
			self._debug_log("State and commands reset completed", 1, "RESET")
	
	# ==================== INTERNAL METHODS ====================
	
	def _process_immediate_commands(self, command: ExecutionCommand, data: Dict[str, Any]):
		"""Process commands that need immediate state changes"""
		self._debug_log(f"Processing immediate state changes for {command.name}", 1, "IMMEDIATE_PROCESS")

		if command == ExecutionCommand.ENABLE_STEP_MODE:
			self._state['step_mode_enabled'] = True
			self._debug_log("Step mode enabled via immediate processing", 1, "STEP_MODE")
		elif command == ExecutionCommand.DISABLE_STEP_MODE:
			self._state['step_mode_enabled'] = False
			self._debug_log("Step mode disabled via immediate processing", 1, "STEP_MODE")
		elif command == ExecutionCommand.CHANGE_LOG_LEVEL:
			self._state['log_level'] = data.get('level', 'INFO')
			self._debug_log(f"Log level changed to {data.get('level', 'INFO')}", 1, "LOG_LEVEL")
		elif command == ExecutionCommand.RESUME:
			# Remove pause command when resume is issued
			self._active_commands.discard(ExecutionCommand.PAUSE)
			self._debug_log("Pause command removed due to resume", 1, "RESUME_PROCESS")
	
	def _trim_history(self):
		"""Keep command history within limits"""
		if len(self._command_history) > self._max_history:
			trimmed_count = len(self._command_history) - self._max_history
			self._command_history = self._command_history[-self._max_history:]
			self._debug_log(f"Command history trimmed: removed {trimmed_count} old entries", 1, "HISTORY_TRIM")
	
	def heartbeat(self):
		"""Update heartbeat timestamp"""
		with self._lock:
			self._last_heartbeat = time.time()
			self._debug_log("Heartbeat updated", 1, "HEARTBEAT")
	
	def get_command_history(self, limit: int = 10) -> List[CommandData]:
		"""Get recent command history"""
		with self._lock:
			history = self._command_history[-limit:].copy()
			self._debug_log(f"Command history requested: {len(history)} entries", 1, "COMMAND_HISTORY")
			return history
	
	# ==================== DEBUG AND ANALYSIS METHODS ====================
	
	def get_command_lifecycle_info(self, command: ExecutionCommand) -> Dict[str, Any]:
		"""Get detailed lifecycle information for a command"""
		with self._lock:
			if command not in self._command_lifecycle:
				self._debug_log(f"No lifecycle info found for {command.name}", 1, "LIFECYCLE_INFO")
				return {}
			
			lifecycle = self._command_lifecycle[command].copy()
			
			# Calculate durations
			if 'issued' in lifecycle and 'processing_started' in lifecycle:
				lifecycle['time_to_processing'] = lifecycle['processing_started'] - lifecycle['issued']
			
			if 'processing_started' in lifecycle and 'acknowledged' in lifecycle:
				lifecycle['processing_duration'] = lifecycle['acknowledged'] - lifecycle['processing_started']
			
			if 'issued' in lifecycle and 'acknowledged' in lifecycle:
				lifecycle['total_duration'] = lifecycle['acknowledged'] - lifecycle['issued']
			
			self._debug_log(f"Lifecycle info retrieved for {command.name}: {len(lifecycle)} events", 1, "LIFECYCLE_INFO")
			return lifecycle

	def debug_command_flow(self, command: ExecutionCommand):
		"""Print detailed command flow analysis"""
		if not self.debug_enabled:
			return
			
		print(f"\n COMMAND FLOW ANALYSIS: {command.name}")
		print("="*50)
		
		lifecycle = self.get_command_lifecycle_info(command)
		if lifecycle:
			print(" Lifecycle Events:")
			for event, timestamp in lifecycle.items():
				if isinstance(timestamp, float):
					formatted_time = time.strftime("%H:%M:%S")
					print(f"   {event}: {formatted_time}")
				else:
					print(f"   {event}: {timestamp}")
		
		# Find command in history
		with self._lock:
			cmd_data = None
			for cmd in reversed(self._command_history):
				if cmd.command == command:
					cmd_data = cmd
					break
			
			if cmd_data:
				print(" Command Status:")
				print(f"   Processing Started: {cmd_data.processing_started}")
				print(f"   Processed: {cmd_data.processed}")
				print(f"   Acknowledged: {cmd_data.acknowledged}")
				print(f"   Response: {cmd_data.response}")
			
			print(f" Currently Active: {command in self._active_commands}")
		
		print("="*50)

	def enable_debug(self):
		"""Enable debug logging"""
		self.debug_enabled = True
		print("ThreadsHandler ----> Debug logging enabled")

	def disable_debug(self):
		"""Disable debug logging"""
		print("ThreadsHandler ----> Debug logging disabled")
		self.debug_enabled = False

	# ==================== DEBUGGING METHODS ====================
	
	def debug_info(self) -> str:
		"""Get debug information"""
		with self._lock:
			active_cmds = [cmd.name for cmd in self._active_commands]
			recent_cmds = [f"{cmd.command.name}({cmd.processed})" for cmd in self._command_history[-5:]]
			
			return """
=== Enhanced Thread Safe State Debug ===
Active Commands: {active_cmds}
Recent Commands: {recent_cmds}
Current State: {self._state}
Last Heartbeat: {time.time() - self._last_heartbeat:.1f}s ago
==========================================
"""

# Global instance
execution_state = EnhancedThreadSafeState()